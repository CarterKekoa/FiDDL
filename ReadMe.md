# FiDDL (Face iD Door Lock)

## Project Overview
Our project aims to make property access more convenient for both our consumer and those that they wish to let into their homes. The goal was to create a system that allowed keyless entry into their home via facial recognition software. Our product provides ease to the consumer in times where the homeowner/guests are in a hurry or have their hands full. In addition to being an overall convenience for the user, our idea was fairly unique. Smart doorbells and locks are commonplace in households that can afford it, but most of them require the user to view an interface in order to interact with the devices. Our goal was to create a more advanced version of these products. Because technology is constantly advancing, we knew that to make a successful product, it would need to stand out. In addition to convenience, our product is one of the only keyless and handsfree locks, so consumers will be drawn to it.  

To achieve the product we strived to create, we used the Nuki Smart Lock, Googles Nest Video Doorbell, Googles Firebase, and OpenCV, in addition to creating our web application. Our web app is called FIDDL (Face ID Door Lock). On the web app, homeowners are able to register, login, add photos, and manage permissions. Guests are able to create an account and add photos as well. Once the photos are added, they are stored in Firebase, which is the database containing the information of every registered user. From there, the photos will be analyzed by the facial recognition software, OpenCV, and the model is able to be trained. Training the model with more photos creates a higher level of accuracy in OpenCV. It will ensure that when a user is at the door, there will be no problems recognizing them. Once a user walks into the frame of the doorbell, images of their face will be captured and cross–checked against the photos stored in the database. If the user has been previously permitted, the door will unlock, otherwise it will remain locked.  

* Test Harness #1 - A simple app that works with the lock API and can unlock and lock the door upon user request.   
* Test Harness #2 - A simple app that can use the facial recognition software and recognize a face with acceptable accuracy.   
* Web Application - A working web app that allows users to create profiles, add photos and invite other members of the database.     
* Doorbell/Smart Lock communication - A demonstrable example of the doorbell communicating with the smart lock to open the door based on a successful match.    
* Functional Prototype - The facial recognition software is fully integrated and able to compare the user uploaded photos to real time Doorbell video to perform facial recognition and determine if the door should be opened. At this point the project will be performing the task we initially purposed.    
* Performance Evaluation Results - A review of the software’s ability to correctly match faces to prerecorded facial data. Keeping the false positive rate low will also be crucial to prevent security breaches.   
* Maintenance Plan - After a working product has been established. This phase would involve “cleaning” up the app to provide for a more satisfying user experience, as well as continually improving security and accuracy.  
* Final Deliverable – A user friendly web application that allows users to create profiles, add photos, and permit users. The doorbell detects faces, cross-matches with photos in the database, and unlocks the lock accordingly.  

## Work Accomplished
Our team proposed and created a keyless entry solution using facial recognition technology. The user, owning a smart lock and a smart doorbell, will register himself as a user on our web application.  

![Register Screen](/static/rdme/Reg.png)

After this registration, they will upload photos of themselves and press a button to train the facial recognition over their photos. They can then choose who they want to be an “admitted” user to their home out of everyone who is currently into our database.    
![User Home Page](/static/rdme/Home.png) 

Then, they simply need to approach the doorbell and it will capture their face and send the image to our application. The application will then run facial recognition software over the photo to determine who is present. If the person at the door is recognized as a permitted user chosen by the owner, the application will send a message to the lock and the door will unlock. All without any interaction from the person at the door.  
We created a web application that is hosted on Heroku and uses Google Firebase as a database for the users and their photos. The web application has some open-source facial recognition software from OpenCV that we optimized to run for our specific needs. This facial recognition software will run over the uploaded photos of the users in our database in order to train a model that can tell one person from another. The homeowner can select which users they want to permit into their home and the application will store those answers in our database to be retrieved when a guest approaches the doorbell. When a guest approaches the doorbell it will take a snapshot either once it recognizes a person or upon the guest pressing the chime button. That snapshot is then sent to the application to be analyzed and the facial recognition software will determine if the person is allowed entry, if they are recognized but not allowed entry, or if they are simply an unknown person. If and only if the person is recognized and allowed entry will the application send a message to the smart lock requesting that it unlock and allow the guest inside. 

 ## System Architecture and Design  
 ![System Architecture Diagram](/static/rdme/Arch.png)  
 The FiDDL web app is written in Python and makes use of the Flask Web Framework to act as a website. This web app stores all the user photos and general information on the Google Firebase server. User information and photos are easily grabbed from the database for use by the web app. A user interacts with the web app and is able to register an account, upload photos, develop a profile, and test some Facial Recognition software (all stored in firebase).  The Doorbell API is configured through the Google Cloud Server to communicate with our web app for any event that the doorbell finds (Person at the door, Chime/Ring, Sound, and Motion). Our web app only looks for a Person/Chime event and then asks Google Cloud for the photo of the person from the event. This photos is ran against the Open CV Facial Recognition and compared to our already trained user data. All the users uploaded photos are trained using OpenCV so that the single event photo can be found to be one or none of our users. Open CV will return the user it thinks is in the photo and how confident it is that that user is in the event photo. Depending on the confidence returned and if the user found is a “permitted person” to the home, FiDDL will use the Nuki Smartlock API to tell it to unlock for the user at the door, thus allowing hands free home access. The entire web app is packaged into a Docker Container and Deployed on Heroku so it can be accessed over the internet from anywhere.   
 
 ![System Design Diagram](/static/rdme/Design.png)  
 Diving Into FiDDL a bit more we can see the packages that we used to complete the project and the packages we created to implement the functionality. Every package we import was also installed in our Virtual Environment Package so that the project is self-contained and can be deployed on the cloud and still maintain its functionality. This also works so that all the team developers can work with the same versions. These Venv packages are absolutely necessary and is even required to run python in general. We also used an OpenCV Package that allowed us to run data analytics and Facial Recognition. Thankfully this ability was opened source and we were able to alter the Facial Recognition specifically for our database and web app. This package is used to train our FR Models on all of our user photos and subsequently determine if any photo afterwards contains a person that is also in the models. Our Auth, User, and General packages are all intended for any web app interactions including logging in, registering, uploading images, training models, etc. These packages are what maintain the database with user information. The Endpoint package we created was specifically made to be a fully automated process that begins once the Google Nest Doorbell tells us an event has fired. This package grabs the image from the doorbell event, runs FR to determine if it’s one of our users, and unlocks the smart lock accordingly. All these packages are connected through the Initialization file that is ran when the web app is started. 

##  Project Delivery, Deployment, and Maintenance 
The FiDDL software runs on a server so to deploy our product, the website simply needs to be hosted. At the moment the software is hard coded to only work with a specific Google Nest doorbell and Nuki smart lock. An improvement to the software would to add a feature to the website to link up the doorbell and smart lock. The application was developed with future maintenance in mind meaning that the code was well documented for easy reading and debugging. For future maintenance, regular updates would be rolled out to users to keep the website in working order. The benefit of a web application means that users do not have to download the update to their personal devices since the website will already be updated when they login.  

## Contributers  
Carter: Web Application, Database, Heroku deployment 
Kevin: Open CV, Database, Heroku deployment
Shawn: Lock implementation, UI improvements
Drew: Doorbell implementation  

 
