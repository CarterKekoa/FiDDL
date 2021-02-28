# USAGE
# python extract_embeddings.py --dataset dataset --embeddings output/embeddings.pickle \
#	--detector face_detection_model --embedding-model openface_nn4.small2.v1.t7

# import the necessary packages
from imutils import paths
import numpy as np
import argparse
import imutils
import pickle
import cv2
import os
import urllib.request
import certifi
import requests

def create_embeddings(locations_dict, name):
	# load our serialized face detector from disk
	print("[INFO] loading face detector...")
	protoPath = os.path.sep.join(["face_detection_model", "deploy.prototxt"])
	modelPath = os.path.sep.join(["face_detection_model",
		"res10_300x300_ssd_iter_140000.caffemodel"])
	detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)
	print("protopath: " + str(protoPath))
	print("modelpath: " + str(modelPath))
	print("detector: " + str(detector))

	# load our serialized face embedding model from disk
	print("[INFO] loading face recognizer...")
	embedder = cv2.dnn.readNetFromTorch("openface_nn4.small2.v1.t7")
	print("embedder: " + str(embedder))

	# grab the paths to the input images in our dataset
	#print("[INFO] quantifying faces...")
	#imagePaths = list(paths.list_images("dataset"))
	#imagePaths = locations_dict
	#print("ImagePaths: " + str(imagePaths))
	#print("dataset: " + str("dataset"))
	
	# initialize our lists of extracted facial embeddings and
	# corresponding people names
	knownEmbeddings = []
	knownNames = []

	# initialize the total number of faces processed
	total = 0
	count = 0

	# loop over the image paths
	print("[INFO] quantifying faces...")
	for key in locations_dict.keys():
			print("key: " + key)
			for val in locations_dict[key]:
				print("val: " + val)

				print("Image Loop Start------------------------------------------------------------------")
				# extract the person name from the image path
				print("[INFO] processing image {}/{}".format(count + 1,
					len(locations_dict[key])))
				#name = imagePath.split(os.path.sep)[-2]	#name is passed in instead
				name = key			# set name to id of the person in photos
				
				# load the image, resize it to have a width of 600 pixels (while
				# maintaining the aspect ratio), and then grab the image
				# dimensions
				
				print("val: " + val)
				#resp = requests.get(val, stream=True).raw
				
				try:

					resp = urllib.request.urlopen(val)
					#print("resp: ",resp)
					image = np.asarray(bytearray(resp.read()), dtype="uint8")
					#print("image0: ", type(image))
					#TODO: get the image url to be able to be read by cv2.imread
					image = cv2.imdecode(image, cv2.IMREAD_COLOR)
					#print("image1: ", type(image))
					#image = cv2.imencode(".png", image)
					
					
					
					#image = cv2.imread(image)
					#print("image2: " + str(image))
					image = imutils.resize(image, width=600)
					#print("image3: " + str(image))
					(h, w) = image.shape[:2]

					# construct a blob from the image
					imageBlob = cv2.dnn.blobFromImage(
						cv2.resize(image, (300, 300)), 1.0, (300, 300),
						(104.0, 177.0, 123.0), swapRB=False, crop=False)

					# apply OpenCV's deep learning-based face detector to localize
					# faces in the input image
					detector.setInput(imageBlob)
					detections = detector.forward()

					# ensure at least one face was found
					if len(detections) > 0:
						# we're making the assumption that each image has only ONE
						# face, so find the bounding box with the largest probability
						count = np.argmax(detections[0, 0, :, 2])
						confidence = detections[0, 0, count, 2]

						# ensure that the detection with the largest probability also
						# means our minimum probability test (thus helping filter out
						# weak detections)
						if confidence > 0.5:
							# compute the (x, y)-coordinates of the bounding box for
							# the face
							box = detections[0, 0, count, 3:7] * np.array([w, h, w, h])
							(startX, startY, endX, endY) = box.astype("int")

							# extract the face ROI and grab the ROI dimensions
							face = image[startY:endY, startX:endX]
							(fH, fW) = face.shape[:2]

							# ensure the face width and height are sufficiently large
							if fW < 20 or fH < 20:
								continue

							# construct a blob for the face ROI, then pass the blob
							# through our face embedding model to obtain the 128-d
							# quantification of the face
							faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255,
								(96, 96), (0, 0, 0), swapRB=True, crop=False)
							embedder.setInput(faceBlob)
							vec = embedder.forward()

							# add the name of the person + corresponding face
							# embedding to their respective lists
							knownNames.append(name)
							knownEmbeddings.append(vec.flatten())
							total += 1
					count += 1
					print("Image Loop End------------------------------------------------------------------")
				except urllib.error.HTTPError:
					print("[ERROR] Bad URL. Ignored.")

	# dump the facial embeddings + names to disk
	print("[INFO] serializing {} encodings...".format(total))
	data = {"embeddings": knownEmbeddings, "names": knownNames}
	print("DATA: ", data)
	f = open("output/embeddings.pickle", "wb")
	print("F: ", f)
	f.write(pickle.dumps(data))
	f.close()


##################### Called from command line #####################
if __name__ == "__main__":
	# construct the argument parser and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--dataset", required=True,
		help="path to input directory of faces + images")
	ap.add_argument("-e", "--embeddings", required=True,
		help="path to output serialized db of facial embeddings")
	ap.add_argument("-d", "--detector", required=True,
		help="path to OpenCV's deep learning face detector")
	ap.add_argument("-m", "--embedding-model", required=True,
		help="path to OpenCV's deep learning face embedding model")
	ap.add_argument("-c", "--confidence", type=float, default=0.5,
		help="minimum probability to filter weak detections")
	args = vars(ap.parse_args())

	# load our serialized face detector from disk
	print("[INFO] loading face detector...")
	protoPath = os.path.sep.join([args["detector"], "deploy.prototxt"])
	modelPath = os.path.sep.join([args["detector"],
		"res10_300x300_ssd_iter_140000.caffemodel"])
	detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

	# load our serialized face embedding model from disk
	print("[INFO] loading face recognizer...")
	embedder = cv2.dnn.readNetFromTorch(args["embedding_model"])

	# grab the paths to the input images in our dataset
	print("[INFO] quantifying faces...")
	imagePaths = list(paths.list_images(args["dataset"]))

	# initialize our lists of extracted facial embeddings and
	# corresponding people names
	knownEmbeddings = []
	knownNames = []

	# initialize the total number of faces processed
	total = 0

	# loop over the image paths
	for (i, imagePath) in enumerate(imagePaths):
		# extract the person name from the image path
		print("[INFO] processing image {}/{}".format(i + 1,
			len(imagePaths)))
		name = imagePath.split(os.path.sep)[-2]

		# load the image, resize it to have a width of 600 pixels (while
		# maintaining the aspect ratio), and then grab the image
		# dimensions
		image = cv2.imread(imagePath)
		image = imutils.resize(image, width=600)
		(h, w) = image.shape[:2]

		# construct a blob from the image
		imageBlob = cv2.dnn.blobFromImage(
			cv2.resize(image, (300, 300)), 1.0, (300, 300),
			(104.0, 177.0, 123.0), swapRB=False, crop=False)

		# apply OpenCV's deep learning-based face detector to localize
		# faces in the input image
		detector.setInput(imageBlob)
		detections = detector.forward()

		# ensure at least one face was found
		if len(detections) > 0:
			# we're making the assumption that each image has only ONE
			# face, so find the bounding box with the largest probability
			i = np.argmax(detections[0, 0, :, 2])
			confidence = detections[0, 0, i, 2]

			# ensure that the detection with the largest probability also
			# means our minimum probability test (thus helping filter out
			# weak detections)
			if confidence > args["confidence"]:
				# compute the (x, y)-coordinates of the bounding box for
				# the face
				box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
				(startX, startY, endX, endY) = box.astype("int")

				# extract the face ROI and grab the ROI dimensions
				face = image[startY:endY, startX:endX]
				(fH, fW) = face.shape[:2]

				# ensure the face width and height are sufficiently large
				if fW < 20 or fH < 20:
					continue

				# construct a blob for the face ROI, then pass the blob
				# through our face embedding model to obtain the 128-d
				# quantification of the face
				faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255,
					(96, 96), (0, 0, 0), swapRB=True, crop=False)
				embedder.setInput(faceBlob)
				vec = embedder.forward()

				# add the name of the person + corresponding face
				# embedding to their respective lists
				knownNames.append(name)
				knownEmbeddings.append(vec.flatten())
				total += 1

	# dump the facial embeddings + names to disk
	print("[INFO] serializing {} encodings...".format(total))
	data = {"embeddings": knownEmbeddings, "names": knownNames}
	f = open(args["embeddings"], "wb")
	f.write(pickle.dumps(data))
	f.close()