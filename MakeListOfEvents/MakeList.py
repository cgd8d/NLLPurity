from __future__ import with_statement
import sys
import math
import ROOT
ROOT.TH1.AddDirectory(False)
ROOT.gROOT.SetBatch()
if ROOT.gSystem.Load("libEXOUtilities") < 0: sys.exit('Failed to load EXOUtilities.')

if len(sys.argv) < 2:
    print 'We need the denoised file glob to be passed in as an argument:'
    print 'python MakeList.py <file path> <tag>_opt'
    sys.exit()
OutStem = 'RotationAngle'
if len(sys.argv) > 2: OutStem += '_' + sys.argv[2]

def GetValueWithID(text, ID):
    import re
    # Define the regular expression for extracting numbers from the log file.
    FloatWithoutExp = '(?:[\-\+]?\d+(?:\.\d+)?)'
    Exp = '(?:e[\-\+]?\d+)'
    FloatPattern = FloatWithoutExp + Exp + '?' # Float, with an optional exponent.

    # Get the float (as a string) tagged as ID.
    output = re.search('\'' + ID + '\': \((' + FloatPattern + ')', text).group(1)

    # Convert to float type, and return.
    return float(output)

# Parse the output file from ComputeRotationAngle to find the single-site peak position and width.
with open(OutStem + '.log') as rotlogfile:
    filecontent = rotlogfile.read()
    Theta = GetValueWithID(filecontent, 'Theta_ss')
    PeakPos = GetValueWithID(filecontent, 'PeakPos_ss')
    Res = GetValueWithID(filecontent, 'Resolution_ss')

LowerBoundE = PeakPos*(1-Res)
UpperBoundE = PeakPos*(1+Res)

# Set up ROOT file.
chain = ROOT.TChain('tree')
chain.Add(sys.argv[1])
event = ROOT.EXOEventData()
chain.SetBranchAddress('EventBranch', event)

# Loop through the file, grabbing usable events.
with open(OutStem + '.txt', 'w') as outfile:
    for i in xrange(chain.GetEntries()):
        chain.GetEntry(i)

        # Lots of reasons we might not keep an event.
        if event.GetNumScintillationClusters() != 1: continue
        if event.GetNumChargeClusters() != 1: continue
        scintcluster = event.GetScintillationCluster(0)
        chargecluster = event.GetChargeCluster(0)
        energy = (math.sin(Theta)*scintcluster.fRawEnergy +
                  math.cos(Theta)*chargecluster.fPurityCorrectedEnergy)
        if energy < LowerBoundE or energy > UpperBoundE: continue
        if (abs(chargecluster.fX) > 200 or
            abs(chargecluster.fY) > 200 or
            abs(chargecluster.fZ) > 200): continue

        # Get the time of the scintillation event.
        time = event.fEventHeader.fTriggerSeconds + float(event.fEventHeader.fTriggerMicroSeconds)/1e6
        time += (scintcluster.fTime - 1024.)/1e6 # Correction for the time of the event within the frame.

        # Print output.
        outfile.write('%f,%f,%f\n' % (chargecluster.fZ,
                                      chargecluster.fCorrectedEnergy,
                                      time))
