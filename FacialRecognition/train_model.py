# USAGE
# python train_model.py --embeddings output/embeddings.pickle \
#	--recognizer output/recognizer.pickle --le output/le.pickle

# import the necessary packages
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
import argparse
import pickle

import fiddl_utils as fiddl_utils


def train():
	print()
	try:
		# load the face embeddings
		print(fiddl_utils.bcolors.OKCYAN, "[TRAIN_MODEL] loading face embeddings...", fiddl_utils.bcolors.ENDC)
		data = pickle.loads(open("output/embeddings.pickle", "rb").read())
		#print("data:", data)

		# encode the labels
		print(fiddl_utils.bcolors.OKCYAN, "[TRAIN_MODEL] encoding labels... ", fiddl_utils.bcolors.ENDC)
		le = LabelEncoder()
		labels = le.fit_transform(data["names"])
		#print("datanames:", data["names"])
		#print("labels:", labels)

		# train the model used to accept the 128-d embeddings of the face and
		# then produce the actual face recognition
		print(fiddl_utils.bcolors.OKCYAN, "[TRAIN_MODEL] training model...", fiddl_utils.bcolors.ENDC)
		recognizer = SVC(C=1.0, kernel="linear", probability=True)
		recognizer.fit(data["embeddings"], labels)

		# write the actual face recognition model to disk
		f = open("output/recognizer.pickle", "wb")
		f.write(pickle.dumps(recognizer))
		f.close()

		# write the label encoder to disk
		f = open("output/le.pickle", "wb")
		f.write(pickle.dumps(le))
		f.close()
		print(fiddl_utils.bcolors.OKCYAN, "[TRAIN_MODEL] Model Trained", fiddl_utils.bcolors.ENDC)
		print()
	except:
		print("[ERROR - TRAIN_MODEL] Error Occured")
		fiddl_utils.PrintException()

if __name__ == "__main__":
	# construct the argument parser and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-e", "--embeddings", required=True,
		help="path to serialized db of facial embeddings")
	ap.add_argument("-r", "--recognizer", required=True,
		help="path to output model trained to recognize faces")
	ap.add_argument("-l", "--le", required=True,
		help="path to output label encoder")
	args = vars(ap.parse_args())

	# load the face embeddings
	print("[INFO] loading face embeddings...")
	data = pickle.loads(open(args["embeddings"], "rb").read())

	# encode the labels
	print("[INFO] encoding labels...")
	le = LabelEncoder()
	labels = le.fit_transform(data["names"])

	# train the model used to accept the 128-d embeddings of the face and
	# then produce the actual face recognition
	print("[INFO] training model...")
	recognizer = SVC(C=1.0, kernel="linear", probability=True)
	recognizer.fit(data["embeddings"], labels)

	# write the actual face recognition model to disk
	f = open(args["recognizer"], "wb")
	f.write(pickle.dumps(recognizer))
	f.close()

	# write the label encoder to disk
	f = open(args["le"], "wb")
	f.write(pickle.dumps(le))
	f.close()