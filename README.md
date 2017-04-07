# Smart Meeting Room Device

## Problem Statement
Not easy to book meeting rooms currently. It’s a tedious process. This device will be hanging at the door of the meeting rooms. If the room is booked the device will display so. Else it will display as empty. The room could be booked for a specified duration by a single button press on the device. Also, sometimes people book the room but don’t use. There would be an occupy button on the device which the users would press upon entering the booked room and a free button which they would press upon leaving the room. Hence, if the user doesn’t use the room, the room can be freed after a certain time or a request can be sent to the meeting organizer to let go of the room in case the user doesn’t require it anymore.

## Tools Used
1. Arduino Lily Pad USB with striped down version of Adobe Tech-summit IOT badge-firmware.
2. Python web server
3. Khoon Paseena

## Current Functionalities

Badge is supposed to be hanging on the outside of meeting room's door. It has following functionalities:
* Generic Function:
 * User can press a button to call housekeeping staff to clean the room. An e-mail is sent to housekeeping department with location details.
 * There is help button on each page (where ever appropriate).
 
* If room is free:
 * This is indicated by green LED lights. 
 * It shows the time till it is free. That is the time before next meeting starts.
 * User can book meeting room for any duration which can selected on the device. Duration should be greater than zero and less than or equal to total time before next meeting.
 * Room gets instantly booked by sending mails to appropriate IDs.

* If room is booked but unoccupied:
 * This is indicated by yellow LED lights. 
 * It shows the time till it is booked.
 * User can press button and mark it as "occupied" after providing suitable authentication. Currently authentication is OTP based. This OTP is provided while booking the room to the organizer and attendees.
 * If the room is unoccupied for long and someone (non-attendee) wants to book the room, he/she can press a button to request the room to be freed. This sends a mail to meeting organizer to free the room.
 * User can press a button to send a meeting reminder to all attendees.
 
* If room is booked and occupied:
 * This is indicated by red LED lights.
 * It shows the time till it is booked.
 * User (organizer/meeting attendees) can press a button to free the room. This is helpful in-case meeting gets cancelled or ends sooner than planned.
 * User can press a button to send a meeting reminder to all attendees.