#!/bin/bash
#SBATCH -J chbd
#SBATCH -N 5
#SBATCH -n 180
#SBATCH --ntasks-per-core=1
#SBATCH --ntasks-per-node=36
#SBATCH --time=00:01:00
#SBATCH --job-name="FREEPROP"


module purge
module load openmpi/gnu/2.0.2.10 chdb/1.0-ompi python/3.6.3
ulimit -s 10240

nruns=359
name=e0d24-g0d370-N150
wdir=/tmpdir/p0110mm/$name-freeprop-${SLURM_JOB_ID}
inputfile=input/$name

python3 freepropaveraged.py initialize $wdir/ 
srun chdb --in-type "0 $nruns" --report "$wdir/report.txt" --command "python3 freepropaveraged.py compute $wdir/ $inputfile $nruns %path%"
python3 freepropaveraged.py average $wdir/ 
python3 freepropaveraged.py plot $wdir/ 
