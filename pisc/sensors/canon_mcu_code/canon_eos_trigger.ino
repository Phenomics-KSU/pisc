#include <stdlib.h>

#include <SPI.h>
#include <usbhub.h>

#include <ptp.h>
#include <canoneos.h>
#include <eoseventdump.h>

// Forward declarations
void reportInWrongState(char const * state);

// Status frame starts and stop strings that report status messages back to client.
char const * const statusStartFrame = "<*<";
char const * const statusEndFrame = ">*>";

class CamStateHandlers : public EOSStateHandlers
{
private:

      enum CamStates { stInitial, stDisconnected, stConnected };
      CamStates   stateConnected;

public:

      // Constructor
      CamStateHandlers() : stateConnected(stInitial) {};
      
      // This state is implemented below to trigger camera.
      virtual void OnDeviceInitializedState(PTP *ptp);
      
       // Other possible states.  First call parent handler, and then if we're trying to trigger the camera in one of them report that it's not going to happen.
      virtual void OnDeviceDisconnectedState(PTP *ptp) { EOSStateHandlers::OnDeviceDisconnectedState(ptp); reportInWrongState("Disconnected"); }
      virtual void OnSessionNotOpenedState(PTP *ptp) { EOSStateHandlers::OnSessionNotOpenedState(ptp); reportInWrongState("Not Opened"); }
      virtual void OnSessionOpenedState(PTP *ptp) { EOSStateHandlers::OnSessionOpenedState(ptp); reportInWrongState("Opened"); }
      virtual void OnDeviceNotRespondingState(PTP *ptp) { EOSStateHandlers::OnDeviceNotRespondingState(ptp); reportInWrongState("Not Responding"); }
      virtual void OnDeviceBusyState(PTP *ptp) { EOSStateHandlers::OnDeviceBusyState(ptp); reportInWrongState("Busy"); }
};

// File scoped instances
static CamStateHandlers    camStates;
static USB                 usb;
static USBHub              usbHub(&usb);
static CanonEOS            eos(&usb, &camStates);

static byte inByte = 0; // Byte read in from serial port.
static bool receivedTriggerCommand = false;
static bool usbInitializedCorrectly = true;
static bool synced_to_client = false; // becomes true when first receive sync command from client.
static uint32_t sync_time = 0; // MCU time that the sync command was received.  In milliseconds.
static uint32_t trigger_period = 0; // Period in milliseconds before triggering camera.  If set to 0 then periodic triggering is disabled.
static uint32_t previous_capture_time = 0; // Time in milliseconds of the last image.  Not the one that was just taken.
static uint32_t last_loop_end_time = 0; // Time in milliseconds that the last camera triggering loop finished at.
static uint32_t successive_image_count = 0; // How many images have been captured without failure or time being re-synced.
const int minimum_loop_time = 750; // Ensures no errors from over triggering.

// Read all bytes from serial buffer.
void clearSerialInputBuffer(void)
{
    while (Serial.available())
    {
        Serial.read();
    }
}

// Trigger camera once command is received. Continuously called when device is connected and initialized.
void CamStateHandlers::OnDeviceInitializedState(PTP *ptp)
{
    EOSEventDump hex; // used for event dump.
    
    int milliseconds_since_last_loop = millis() - last_loop_end_time;
    
    if (milliseconds_since_last_loop < minimum_loop_time)
    {
        return; // Limit max rate that function runs.
    }
    
    if (trigger_period > 0)
    {
        if (milliseconds_since_last_loop > trigger_period)
        {
            receivedTriggerCommand = true; // time to take a picture
        }
    }
    
    if (!receivedTriggerCommand)
    {
        return; // Don't want to take picture.
    }
    
    // Reset flag so we don't keep triggering.
    receivedTriggerCommand = false;
    
    // If we've already taken a picture then send back event dump which will contain that last filename.
    // Safer to do here than after taking a picture since this ensures the max elapsed time before event dump.
    if (successive_image_count >= 1)
    {
        // Send back image filename of the picture we took last time (and also a bunch of other data)
        Serial.print(statusStartFrame);
        Serial.print("dump-");
        eos.EventCheck(&hex);
        Serial.println(statusEndFrame);
        
        // Send back elapsed time of previous image since that's what the filename in the event dump is for.
        // Even though shouldn't happen make sure last capture time is greater than sync time to avoid rollover right after sync.
        uint32_t time_since_sync = 0;
        if (previous_capture_time > sync_time)
        {
            time_since_sync = previous_capture_time - sync_time; 
        }
        printTimeMessage(time_since_sync);
  
    }
    else // haven't taken a successful picture yet.
    {
        // dump any old information so old filenames don't get sent out next dump.
        // Don't wrap in frame so client doesn't pick it up as an actual event dump.
        // Delay afterwards to give camera some time before triggering.  Otherwise camera can get upset.
        Serial.print("trash-");
        eos.EventCheck(&hex);
        delay(300);
    }
    
    uint32_t capture_time = millis();
    
    uint16_t ptp_return = eos.Capture();

    // Clear any previous requests for triggering.  This allows client to send multiple requests at once to ensure one gets received.
    //clearSerialInputBuffer(); // KLM disabled because different types of commands are being sent now.
    
    if (ptp_return == PTP_RC_OK)
    {
        successive_image_count++;
        
        // Update previous capture so can use it for next time.
        previous_capture_time = capture_time;  
    }
    else
    {
        // Send failure status report.
        printStatusMessage("Trigger failure: " + String(ptp_return, HEX));
        
        // Reset count since we had a failure. 
        successive_image_count = 0;
    }
    
    last_loop_end_time = millis();

}

// Send 'state' text back over serial port if we're trying to take a picture.  Should be called from non-triggering states.
void reportInWrongState(char const * state)
{
    if (receivedTriggerCommand) 
    {
        printStatusMessage(state);
    }
}

// Send status message over serial port starting and stopping with frame.
void printStatusMessage(String message)
{
    Serial.print(statusStartFrame);
    Serial.print("status-" + message);
    Serial.println(statusEndFrame);
}

// Overload for character array.
void printStatusMessage(char const * message)
{
    printStatusMessage(String(message));
}

// Send time message over serial port starting and stopping with frame.
void printTimeMessage(uint32_t time)
{
    Serial.print(statusStartFrame);
    Serial.print("time-" + String(time));
    Serial.println(statusEndFrame);
}

// Return new line terminated string from serial port. Newline not included.
void readSerialLine(char * newLineBuffer, int max_length)
{
    int rx_index = 0;
    while (true)
    {
        if (Serial.available())
        {
            if (rx_index >= (max_length-1))
            {
                break; // no more room in buffer
            }
            
            byte inChar = Serial.read();
            
            newLineBuffer[rx_index] = inChar;
            rx_index++;
            if (inChar == '\n')
            {
                newLineBuffer[rx_index] = '\0';
                return; // hit end of string.
            }
        }
    } 
}

void setup()
{
    Serial.begin(57600);

    if (usb.Init() == -1)
    {
        usbInitializedCorrectly = false;
        printStatusMessage("OSC did not start.");
    }
    
    clearSerialInputBuffer();

    delay(200);
}

void loop()
{
    if (!usbInitializedCorrectly)
    {
        // Report USB failure status.
        printStatusMessage("USB Failure. Please reset.");
        delay(1000);
        return;
    }

    if (Serial.available() > 0)
    {
        inByte = Serial.read();
        
        if (inByte == 's') // sync command
        {
            sync_time = millis();
            if (synced_to_client)
            {
                printStatusMessage("Resynced");
            }
            synced_to_client = true;
            successive_image_count = 0; // reset count so will wait at least one picture before sending back image name / time.
            Serial.print('a'); // acknowledge
        }
        else if (inByte == 't') // trigger command
        {
            receivedTriggerCommand = true;
        }
        else if (inByte == 'p') // change periodic trigger command
        {
            char period_buffer[20];
            readSerialLine(period_buffer, 20);
            //Serial.print(String(period_buffer));
            //printStatusMessage("Trigger period received:  " + String(period_buffer));
            int new_period = atoi(period_buffer);
            if (new_period != trigger_period)
            {
                printStatusMessage("New trigger period: " + String(new_period));
            }
            if (new_period != 0 && new_period < minimum_loop_time)
            {
                printStatusMessage("New period of " + String(new_period) + " is less than minimum loop time of " + String(minimum_loop_time));
            }
            else // new trigger time is valid
            {
                trigger_period = new_period;
            }
            //Serial.print(String(new_period)); // ack
        }
        else 
        {
            //printStatusMessage("Invalid Byte: " + String(inByte));
        }
    }
  
    // Execute state machine
    usb.Task();
}
