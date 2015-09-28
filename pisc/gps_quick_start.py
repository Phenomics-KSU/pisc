'''
Created on Jun 2, 2015

@author: ejwel_000
'''



import os 


if __name__ == '__main__':
    pass

# Change active directory to location of gps_startup.py
os.chdir('C:\Users\ejwel_000\Workspaces\PISC\pisc\pisc')
# open new cmd window and run gps_startup.py with the arguments
os.system('start /wait cmd /c python gps_startup.py -f ../nmea_logs/gga.txt -s 2')



