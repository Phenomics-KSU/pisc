#include <SPI.h>
#include <usbhub.h>

#include <ptp.h>
#include <canoneos.h>
#include <eoseventdump.h>

// Forward declarations
void reportInWrongState(char const * state);

// Status frame starts and stop strings that report status messages back to client.
char const * const statusFrame = "<<%>>";

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
static uint32_t last_capture_attempt = 0;

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
    if (!receivedTriggerCommand)
    {
        return; // Don't want to take picture.    
    }
    
    // Reset flag so we don't keep triggering.
    receivedTriggerCommand = false;
    
    uint16_t ptp_return = eos.Capture();
    
    // Adding a short delay seems to fix an issue where the camera would randomly revert to a 'not opened' state.
    delay(200);
    
    // Clear any previous requests for triggering.  This allows client to send multiple requests at once to ensure one gets received.
    clearSerialInputBuffer();
    
    if (ptp_return == PTP_RC_OK)
    {
        // Send back last image name (not the one we just took) and also a bunch of other data.
        Serial.print(statusFrame);
        EOSEventDump hex;
        //eos.GetDeviceInfoEx(&hex);
        eos.EventCheck(&hex);
        Serial.println(statusFrame);
    }
    else
    {
        // Send failure status report.
        Serial.print(statusFrame);
        Serial.print("Failure");
        Serial.print(ptp_return, HEX);
        Serial.println(statusFrame);
    }
}

// Send 'state' text back over serial port if we're trying to take a picture.  Should be called from non-triggering states.
void reportInWrongState(char const * state)
{
    if (receivedTriggerCommand) 
    {
        Serial.print(statusFrame);
        Serial.print(state);
        Serial.println(statusFrame);
    }
}

void setup()
{
    Serial.begin(115200);

    if (usb.Init() == -1)
    {
        usbInitializedCorrectly = false;
        Serial.println("OSC did not start.");
    }
    
    clearSerialInputBuffer();

    delay(200);
}

void loop()
{
    if (!usbInitializedCorrectly)
    {
        // Report USB failure status.
        Serial.print(statusFrame);
        Serial.print("USB Failure");
        Serial.println(statusFrame);
        delay(1000);
        return;
    }

    if (Serial.available() > 0)
    {
        inByte = Serial.read();
        
        if (inByte == 'a') // This is the special trigger character.
        {
            receivedTriggerCommand = true;
        }
        else 
        {
            Serial.print(statusFrame);
            Serial.print("Invalid Byte: ");
            Serial.print(inByte);
            Serial.println(statusFrame);
        }
    }
  
    // Execute state machine
    usb.Task();
}
