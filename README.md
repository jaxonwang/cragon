
<p align="center">
  <img src="https://user-images.githubusercontent.com/10634580/86003065-37858700-ba4c-11ea-8d3d-f268497a4e6e.png" />
</p>

# Cragon

[![Build Status](https://travis-ci.com/jaxonwang/cragon.svg?branch=master)](https://travis-ci.com/jaxonwang/cragon)

Cragon is a checkpoint/restart manager for Linux environment. It saves your time whenever you are waiting for a long running scientific computing application in HPC environments. 
When you need to submit/execute a long-running program, do you:
- Don't know how many resources (CPU, memory) the program will need.
- Having been waiting for days, weeks but the program exceeds the maximum time you allowed and killed?
- Having been waiting for days, weeks but the program crashed because it runs out the resources, especially, memory?
- You restart the program, double the resources but still worried about the failure?

Time to try checkpoint/restore for your program! [DMTCP](http://dmtcp.sourceforge.net/) is a robust, powerful, and widely used user-space distributed checkpoint/restore tool in Linux. Neither recompiling nor root-privilege needed, users just backup their processes easily. Cragon uses DMTCP to perform checkpoint/restore, also, providing features below:

- Easy to install and use
- Diagnose the causes of failure of scientific computing applications.
- Only the recoverable will be restart, ex. A process crashed by malloc error.
- Speed up checkpoint by leveraging computing machines' highspeed local storage(such as SSD, NVME).
- Automatically migrate and revive the failed processes to other machines.
- HPC job engines, such as Slurm, UGE.
- Workflow integration.

## Installation
Cragon should be run on Linux kernel >= 2.6.32. Python3 and C++11 compiler are required. It is highly recommended to install Cragon in Python virtualenv or [Conda](https://docs.conda.io/en/latest/).

To enable python virtualenv:
```
$ python3 -m venv newenvname
$ source ./newenvname/bin/activate
(newenvname) $ # now install cragon
```
To install:
```
git clone --recursive https://github.com/jaxonwang/cragon/
cd cragon
python3 setup.py install
```
To run tests:
```
pip install -r test-requirements.txt
tox
```

## Usage
To allow Cragon automatically checkpoint the process, start your progam with:
```
cragon run ./a.out
```

If your program runs long enough to be checkpointed by Cragon, you will see a new directory created by Cragon in current working directory:

And its content:
```
username@hostname:~/cragon$ find cragon_a.out_2020-06-24_18\:52\:15\,344120/
cragon_a.out_2020-06-24_18:52:15,344120/
cragon_a.out_2020-06-24_18:52:15,344120/intercepted.log
cragon_a.out_2020-06-24_18:52:15,344120/process_metrics.json
cragon_a.out_2020-06-24_18:52:15,344120/cragon.log
cragon_a.out_2020-06-24_18:52:15,344120/system_metrics.csv
cragon_a.out_2020-06-24_18:52:15,344120/checkpoint_images
cragon_a.out_2020-06-24_18:52:15,344120/checkpoint_images/1_username@hostname
cragon_a.out_2020-06-24_18:52:15,344120/checkpoint_images/1_username@hostname/ckpt_a.out_c417f7-40000-58163e7382ed.dmtcp
cragon_a.out_2020-06-24_18:52:15,344120/checkpoint_images/1_username@hostname/checkpoint_info
cragon_a.out_2020-06-24_18:52:15,344120/checkpoint_images/2_username@hostname
cragon_a.out_2020-06-24_18:52:15,344120/checkpoint_images/2_username@hostname/ckpt_a.out_c417f7-40000-58163e7382ed.dmtcp
cragon_a.out_2020-06-24_18:52:15,344120/checkpoint_images/2_username@hostname/checkpoint_info
```
The directory ```craong_program_date/checkpoint_images/``` stores the images checkpointed. 
To restart from the latest checkpoint:
```
cragon restart -w ./cragon_a.out_2020-06-24_18:52:15,344120
```
To restart from a specified image:
```
cragon restart ./cragon_a.out_2020-06-24_18:52:15,344120/checkpoint_images/2_username@hostname/
```
If you want to place the images in a different directory:
```
cragon run -w /dirpath/ ./a.out
```
For other usages, please check the help information of Cragon:
```
cragon --help
```
## How it works
Cragon intercepts the libc memory related functions (malloc, mmap, brk) and will know immediatly when the heap memory allocation fails. This will only happen on the systems where memory overcommit is disabled. Luckly, most HPC environments satisfy that. For memory over-commit allowed system, ```ulimit``` might be used to trigger the allocation failure if possible.
## Limitations
Cragon can only mangage programs which are dynamicly linked to libc since DMTCP uses LD_PRELOAD environment variable to acheive the checkpoint/restore.
## Contributing
Cragon is still in its early developing state. There are many features to be implemented. Also please don't hesitate to contact me if you want some new features to be added into Cragon. Cragon won't be complete without feedbacks in real scenarios. If you find some bugs, please new an issue. Any contributions are welcomed and appreciated.

## Licence
MIT
