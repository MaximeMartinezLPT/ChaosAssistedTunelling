#!/bin/bash
#SBATCH -J chbd
#SBATCH -N 5
#SBATCH -n 180
#SBATCH --ntasks-per-core=1
#SBATCH --ntasks-per-node=36
#SBATCH --time=00:45:00
#SBATCH --job-name="nu-heff-beta"


module purge
module load openmpi/gnu/2.0.2.10 chdb/1.0-ompi python/3.6.3
ulimit -s 10240

nruns=179
name=e0d40-g0d310
wdir=/tmpdir/p0110mm/cat-LCAR/nu-heff-beta-$name-${SLURM_JOB_ID}
inputfile=input/$name

python3 nu-heff-beta.py initialize $wdir/
srun chdb --in-type "1 $nruns" --report "$wdir/report.txt" --command "python3 nu-heff-beta.py compute $wdir/ $inputfile $nruns %path%"
python3 nu-heff-beta.py final $wdir/
