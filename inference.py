import sys
import gzip
import shutil
import os
import time

if (len(sys.argv) < 6):
	print("You must give 6 parameters: model_path, features_path, labels_path, channeling, fits_path, species_no")
	print("e.g. python inference.py llda_models/model_hot_cores_full_500it/ llda_train_input/hot_cores_full_features.dat llda_train_input/hot_cores_full_labelmap.sub 5 ../FITS/DMTau.CS_5-4.image.fits 12")
	sys.exit(1)

model = os.path.basename(os.path.normpath(sys.argv[1]))
features = os.path.basename(os.path.normpath(sys.argv[2]))
labels = os.path.basename(os.path.normpath(sys.argv[3]))
channeling = sys.argv[4]
fits_path = sys.argv[5]
species_no = sys.argv[6].split(',')
plot = sys.argv[7] if len(sys.argv) > 7 else ''

#filename = os.path.basename(os.path.normpath(fits_path))
filename = fits_path
temp_filename = "spectrum_document"

start_time = time.time()

#shutil.copyfile(fits_path,"./scripts/"+filename)
os.chdir("./scripts/")
os.system("python llda_parser.py "+filename+" "+channeling+" "+"../llda_train_input/"+features+" "+plot)
#os.system("python csv2spectrum.py ../Schilke_OrionSurvey.csv "+channeling+" "+"../llda_train_input/"+features+" 1,100")

start_time_lda = time.time()
print("Used model: "+model)
with open(temp_filename+".dat", 'rb') as f_in, gzip.open(temp_filename+".dat.gz", 'wb') as f_out: #Must copy to "./llda_models/models/" beacause of some rules that read files in JGibbLabeledLDA
    shutil.copyfileobj(f_in, f_out)
os.remove(temp_filename+".dat")
#os.remove(filename)
os.rename(temp_filename+".dat.gz","../llda_models/"+model+"/"+temp_filename+".dat.gz")

#Model Inference
#Labeled LDA in Java Copyright (C) 2008-2013 Myle Ott (Labeled LDA), Xuan-Hieu Phan and Cam-Tu Nguyen (JGibbLDA)
os.chdir("../JGibbLabeledLDA-master/")
os.system("java -mx8192M -cp bin:lib/args4j-2.0.6.jar:lib/trove-3.0.3.jar jgibblda.LDA -inf -dir ../llda_models/"+model+"/ -model "+model+" -niters 200 -twords 10 -dfile "+temp_filename+".dat.gz")

os.chdir("../llda_models/"+model+"/")
os.remove(temp_filename+".dat.gz")
os.rename(temp_filename+".dat."+model+".theta.gz", "../../scripts/"+temp_filename+".dat."+model+".theta.gz")
#os.system("rm "+temp_filename+".dat."+model+".*")

#Parsing llda output
os.chdir("../../scripts/")
shutil.copyfile("../llda_train_input/"+labels,labels)
os.system("python llda_output_theta_parser.py "+temp_filename+".dat."+model+".theta.gz "+labels+" > ../output.dat")
os.remove(labels)
os.remove(temp_filename+".dat."+model+".theta.gz")

os.chdir("../")
#Evaluate Prediction
match = False
#os.system("cat output.dat")
with open('output.dat') as f:
	last_pos = f.tell()
	last_line = f.readlines()[-1]
	f.seek(last_pos)
	for i,line in enumerate(f):
		#TOP 5
		if i>=5:
			break
		no = line.split()[0].split(';')[1]
		transition_name = " ".join(line.split(';')[1].split()[1:])
		prob = line.split()[-1].split(';')[1]
		last_prob = last_line.split()[-1].split(';')[1]
		
		if no in species_no and prob != last_prob:
			print("Prob: "+str(prob)+" Last Prob: "+str(last_prob))
			response = "¡MATCH in TOP@"+str(i+1)+"! For "+transition_name+"("+str(no)+")"+" Model["+model+"] FITS["+filename+"]: "+prob+"\n"
			with open("matches.out","a") as fileMatch:
				fileMatch.write(response)
			print(response)
			match = True
if (not match):
	print("Transition not found")

end_time_lda = time.time()
print("L-LDA inference time: "+str(end_time_lda-start_time_lda)+" seconds")

end_time = time.time()

print("Total execution time: "+str(end_time-start_time)+" seconds\n")