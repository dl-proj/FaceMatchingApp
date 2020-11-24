# ID_CARD_DETECTION_SYSTEM

## Overview

This project is to calculate the age from human faces and allow user to be available for the system.
This project consists of 2 main sub systems - server and client. The server system is running on LattePanda, while the 
client server system is running on Raspberry Pi 4.

In the server system, first, after project detects the human face, then recognize his age. If his age is in acceptable 
range, it passes the user, but if not, server sends the command to extract the correct age from his card to the client 
system.

The client system is waiting for the server system's command. If it receives the command, then it needs the user shows 
his card(Driver License, ID Card or Passport). Then after it extracts the correct age from his card, it estimates if he 
is a acceptable man or not and returns the result to the server.

This project uses the Sqlite3 database and the GUI of this project has been developed by PyQt.

## Structure

- database
    
    The face database for this project
    
- models

    The several models for age and face detection
    
- src

    The source code for client and server system

- utils

    The source code for face detection, management of folder and files in this project, led management on board, etc.
    
- app

    The main execution file
    
- config

    The configuration file for server & client device.

- settings

    The several settings for model path and server/client selection

- requirements_server
    
    All the dependencies for the server system

- requirements_client

    All the dependencies for the client system

## Installation

- Environment

    Windows 10 on LattePanda, Raspbian on Raspberry Pi, Python 3.6+
    
- Dependency Installation

    Please go ahead to this project directory and run the following command on the terminal according the server/client system.
    
    * Server
        
        ```
        pip3 install -r requiremetns_server.txt
        ```
      
    * client
        ```
        pip3 install -r requirements_client.txt
        ```
- Database Installation

    On the LattePanda, after installing Sqlite3, please make new folder named "database" in this project directory and 
    copy the face database named "face_db.db" into the new database folder.

## Execution

- Please run the following command in this project directory on terminal

    * Server

        ```
        python3 app_server.py
        ```
    * client
        
        ```
        python3 app_client.py
        ```

## Note

- Once the device is fixed, please don't change the values in config file.
