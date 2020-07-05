import sys
import pathlib
import os	
import shutil
import subprocess as sp
import uuid
import random
import datetime

def get_files_in_dir(directory):   
    file_list = [] 

    for x in directory.iterdir():
        if x.is_file():
           file_list.append(x)
        else:
           file_list.append(searching_all_files(directory/x))

    return file_list

def clearFolder(pth): 
    for child in pth.glob('*'):
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)

def oggToMp3(ogg_path, intermed_dir):
	mp3_full_dir = intermed_dir/'mp3_full'
	mp3_name = ogg_path.stem + '.mp3'

	os.chdir(ogg_path.parents[0])

	print('CONVERTING {} TO {}'.format(ogg_path.name, mp3_name))
	cmd = 'ffmpeg -hide_banner -i {} {}'.format(ogg_path.name, mp3_name)
	sp.call(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)

	shutil.move(mp3_name, str(mp3_full_dir))

	return pathlib.Path(mp3_full_dir, mp3_name)

def mp3ToCuts(mp3_path, cuts_length):
	mp3_cuts_dir = intermed_dir/'mp3_cuts'
	os.chdir(mp3_path.parents[0])
	print('CUTTING {} INTO PIECES'.format(mp3_path.name))
	cut_id = uuid.uuid4() 
	cmd = 'ffmpeg -hide_banner -i {} -c pcm_s16le -map 0 -f segment -fflags +genpts -segment_time {} %d_{}_{}_seg.mov'.format(mp3_path.name, cuts_length, cut_id, mp3_path.stem)
	sp.call(cmd, stdout=sp.PIPE, shell=True)

	mp3_files = get_files_in_dir(mp3_path.parents[0])
	
	# add new cuts
	for mp3_file in mp3_files:
		if mp3_file.stem[-3:] == 'seg':
			shutil.move(str(mp3_file), str(mp3_cuts_dir))

def shufleConcatCuts(intermed_dir, cut_length):
	mp3_cuts_dir = intermed_dir/'mp3_cuts'
	output_dir = intermed_dir.parents[0]/'output'

	concat_list_path = pathlib.Path(mp3_cuts_dir, 'concat_list.txt')
	cuts = get_files_in_dir(mp3_cuts_dir)
	shuffled_cuts_win_path = random.sample(cuts, len(cuts))
	shuffled_cuts = map(lambda p: str(p.name), shuffled_cuts_win_path) 

	cut_id = uuid.uuid4()
	# del old cuts in the concat_list
	open(concat_list_path, 'a').close()

	for cut in shuffled_cuts:
		with open(concat_list_path, 'a') as concat_list:
			concat_list.write('file {}\n'.format(cut))
			# concat_list.write('duration {}\n'.format(cut_length))
	now = datetime.datetime.now()
	time =  "%s%s%s" % (now.hour, now.minute, now.microsecond)
	os.chdir(mp3_cuts_dir)
	cmd1 = 'ffmpeg -hide_banner -f concat -safe 0 -i concat_list.txt -c:v copy output_{}.mp4'.format(time)
	sp.call(cmd1, stdout=sp.PIPE, shell=True)
	cmd2 = 'ffmpeg -hide_banner -i output_{}.mp4 -q:a 0 -map a output_{}.mp3'.format(time, time)
	sp.call(cmd2, stdout=sp.PIPE, shell=True)
	

	shutil.move(str('output_{}.mp3'.format(time)), str(output_dir))

	print('\n\n\n OUTPUT FILE PATH {} \n\n'.format(str(output_dir/'output_{}.mp3'.format(time))))


if len(sys.argv) != 2:
	print('Set cut length')
	exit()

cut_length = sys.argv[1]

curr_dir = pathlib.Path(__file__).parent.absolute()
input_dir = curr_dir/'input'
intermed_dir = curr_dir/'intermed'
mp3_cuts_dir = intermed_dir/'mp3_cuts'
output_dir = curr_dir/'output'

ogg_files = []
mp3_files = []

input_files = get_files_in_dir(input_dir)

# Clear old mp3 before creating new
mp3_full_dir = intermed_dir/'mp3_full'
clearFolder(mp3_full_dir)

for filename in input_files:
	if filename.suffix == ".ogg":
		ogg_files.append(filename)
	elif filename.suffix == ".mp3":
		mp3_files.append(filename)

for ogg_file in ogg_files:
	mp3_path = oggToMp3(ogg_file, intermed_dir)
	mp3_files.append(mp3_path)

# del old cuts
clearFolder(mp3_cuts_dir)

for mp3_file in mp3_files:
	mp3ToCuts(mp3_file, cut_length)

# concat cuts
shufleConcatCuts(intermed_dir, cut_length)

