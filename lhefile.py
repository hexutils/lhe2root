import abc
import collections
import re

if __name__ == "__main__":
  import argparse, itertools, sys, unittest
  from .mela import TVar
  parser = argparse.ArgumentParser()
  parser.add_argument('--lhefile-hwithdecay')
  parser.add_argument('--lhefile-hwithdecayonly')  
  parser.add_argument('--lhefile-jhugenvbfvh')
  parser.add_argument('--lhefile-jhugentth')
  parser.add_argument('unittest_args', nargs='*')
  args = parser.parse_args()

import ROOT

from mela import Mela, SimpleParticle_t, SimpleParticleCollection_t

InputEvent = collections.namedtuple("InputEvent", "daughters associated mothers isgen")

class LHEEvent(object, metaclass=abc.ABCMeta):
  def __init__(self, event, isgen):
    lines = event.split("\n")

    self.weights = {}
    for line in lines:
      if "<wgt" not in line: continue
      match = re.match("<wgt id='(.*)'>([0-9+Ee.-]*)</wgt>", line)
      if match: self.weights[match.group(1)] = float(match.group(2))

    lines = [line for line in lines if not ("<" in line or ">" in line or not line.split("#")[0].strip())]
    nparticles, _, weight, _, _, _ = lines[0].split()

    nparticles = int(nparticles)
    self.weight = float(weight)
    if nparticles != len(lines)-1:
      raise ValueError("Wrong number of particles! Should be {}, have {}".format(nparticles, len(lines)-1))

    daughters, associated, mothers = (SimpleParticleCollection_t(_) for _ in self.extracteventparticles(lines[1:], isgen))
    if not list(mothers): mothers = None
    self.daughters, self.associated, self.mothers, self.isgen = self.inputevent = InputEvent(daughters, associated, mothers, isgen)

  @abc.abstractmethod
  def extracteventparticles(cls, lines, isgen): "has to be a classmethod that returns daughters, associated, mothers"

  def __iter__(self):
    return iter(self.inputevent)

class LHEEvent_Hwithdecay(LHEEvent):
  @classmethod
  def extracteventparticles(cls, lines, isgen):
    daughters, mothers, associated = [], [], []
    ids = [None]
    mother1s = [None]
    mother2s = [None]
    for line in lines:
      id, status, mother1, mother2 = (int(_) for _ in line.split()[0:4])
      ids.append(id)
      if (1 <= abs(id) <= 6 or abs(id) == 21) and not isgen:
        line = line.replace(str(id), "0", 1)  #replace the first instance of the jet id with 0, which means unknown jet
      mother1s.append(mother1)
      mother2s.append(mother2)
      if status == -1:
        mothers.append(line)
      elif status == 1 and (1 <= abs(id) <= 6 or 11 <= abs(id) <= 16 or abs(id) in (21, 22)):
        while True:
          if mother1 != mother2 or mother1 is None:
            associated.append(line)
            break
          if ids[mother1] in (25, 39):
            daughters.append(line)
            break
          mother2 = mother2s[mother1]
          mother1 = mother1s[mother1]

    if not isgen: mothers = None
    return daughters, associated, mothers


class LHEEvent_VHHiggsdecay(LHEEvent):
  @classmethod
  def extracteventparticles(cls, lines, isgen):
    daughters, mothers, associated = [], [], []
    ids = [None]
    mother1s = [None]
    mother2s = [None]
    for line in lines:
      id, status, mother1, mother2 = (int(_) for _ in line.split()[0:4])
      ids.append(id)
      
      #if (1 <= abs(id) <= 6 or abs(id) == 21) and not isgen:
      #  line = line.replace(str(id), "0", 1)  #replace the first instance of the jet id with 0, which means unknown jet
      mother1s.append(mother1)
      mother2s.append(mother2)
      if status == -1:
        mothers.append(line)
      elif status == 1 and (1 <= abs(id) <= 6 or 11 <= abs(id) <= 16 or abs(id) in (21, 22)):
        
          if mother1 is None or ids is None or mother1s[mother1] is None :
            #associated.append(line)
            continue
          
          if mother1 == mother2 and abs(ids[mother1]) in (23,24) and  not ids[mother1s[mother1]] == 25 :
            associated.append(line)
            
          
          if mother1 == mother2 and abs(ids[mother1]) == 23 and  ids[mother1s[mother1]] == 25:
            daughters.append(line)
            
    if not isgen: mothers = None
    return daughters, associated, mothers


  
class LHEEvent_HwithdecayOnly(LHEEvent):
  @classmethod
  def extracteventparticles(cls, lines, isgen):
    daughters, mothers, associated = [], [], []
    ids = [None]
    mother1s = [None]
    mother2s = [None]
    for line in lines:
      id, status, mother1, mother2 = (int(_) for _ in line.split()[0:4])
      ids.append(id)
      if (1 <= abs(id) <= 6 or abs(id) == 21) and not isgen:
        line = line.replace(str(id), "0", 1)  #replace the first instance of the jet id with 0, which means unknown jet
      mother1s.append(mother1)
      mother2s.append(mother2)
      if(abs(id) == 22 ):
        associated.append(line)
      #1 <= abs(id) <= 6 or
      if ( 11 <= abs(id) <= 16 ):
          daughters.append(line)
          #if args.merge_photon:
          #  print line

    if not isgen: mothers = None

    return daughters, associated, mothers



  
class LHEEvent_StableHiggs(LHEEvent):
  @classmethod
  def extracteventparticles(cls, lines, isgen):
    daughters, mothers, associated = [], [], []
    for line in lines:
      id, status, mother1, mother2 = (int(_) for _ in line.split()[0:4])
      if (1 <= abs(id) <= 6 or abs(id) == 21) and not isgen:
        line = line.replace(str(id), "0", 1)  #replace the first instance of the jet id with 0, which means unknown jet
      if status == -1:
        mothers.append(line)
      if id == 25:
        if status != 1:
          raise ValueError("Higgs has status {}, expected it to be 1\n\n".format(status) + "\n".join(lines))
        daughters.append(line)
      if abs(id) in (0, 1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 16, 21) and status == 1:
        associated.append(line)

    if len(daughters) != 1:
      raise ValueError("More than one H in the event??\n\n"+"\n".join(lines))
    if cls.nassociatedparticles is not None and len(associated) != cls.nassociatedparticles:
      raise ValueError("Wrong number of associated particles (expected {}, found {})\n\n".format(cls.nassociatedparticles, len(associated))+"\n".join(lines))
    if len(mothers) != 2:
      raise ValueError("{} mothers in the event??\n\n".format(len(mothers))+"\n".join(lines))

    if not isgen: mothers = None
    return daughters, associated, mothers

  nassociatedparticles = None

class LHEEvent_StableHiggsVH(LHEEvent):
  @classmethod
  def extracteventparticles(cls, lines, isgen):
    daughters, mothers, associated = [], [], []
    ids = [None]
    mother1s = [None]
    mother2s = [None]
    for line in lines:
      id, status, mother1, mother2 = (int(_) for _ in line.split()[0:4])
      ids.append(id)

      #if (1 <= abs(id) <= 6 or abs(id) == 21) and not isgen:
      #  line = line.replace(str(id), "0", 1)  #replace the first instance of the jet id with 0, which means unknown jet
      mother1s.append(mother1)
      mother2s.append(mother2)
      if status == -1:
        mothers.append(line)
      elif id == 25:
        daughters.append(line)
      elif status == 1 and (1 <= abs(id) <= 6 or 11 <= abs(id) <= 16 or abs(id) in (21, 22)):

          if mother1 is None or ids is None or mother1s[mother1] is None :
            #associated.append(line)
            continue

          if mother1 == mother2 and abs(ids[mother1]) in (23,24) and not ids[mother1s[mother1]] == 25 :
            associated.append(line)
 
          #elif mother1!= mother2:
            #associated.append(line)

    if not isgen: mothers = None
    return daughters, associated, mothers


class LHEEvent_StableHiggsZHHAWK(LHEEvent):
  @classmethod
  def extracteventparticles(cls, lines, isgen):
    daughters, mothers, associated = [], [], []
    for line in lines:
      id, status, mother1, mother2 = (int(_) for _ in line.split()[0:4])
      if (1 <= abs(id) <= 6 or abs(id) == 21) and not isgen:
        line = line.replace(str(id), "0", 1)  #replace the first instance of the jet id with 0, which means unknown jet
      if status == -1:
        mothers.append(line)
      if id == 25:
        if status != 1:
          raise ValueError("Higgs has status {}, expected it to be 1\n\n".format(status) + "\n".join(lines))
        daughters.append(line)
      if abs(id) in (0, 1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 16, 21,22) and status == 1:
        associated.append(line)

    if len(daughters) != 1:
      raise ValueError("More than one H in the event??\n\n"+"\n".join(lines))
    if cls.nassociatedparticles is not None and len(associated) != cls.nassociatedparticles:
      raise ValueError("Wrong number of associated particles (expected {}, found {})\n\n".format(cls.nassociatedparticles, len(associated))+"\n".join(lines))
    if len(mothers) != 2:
      raise ValueError("{} mothers in the event??\n\n".format(len(mothers))+"\n".join(lines))

    if not isgen: mothers = None
    return daughters, associated, mothers

  nassociatedparticles = None


  
class LHEEvent_JHUGenVBFVH(LHEEvent_StableHiggs):
  nassociatedparticles = 2

class LHEEvent_JHUGenttH(LHEEvent_StableHiggs):
  nassociatedparticles = 6

class LHEEvent_Offshell4l(LHEEvent):
  @classmethod
  def extracteventparticles(cls, lines, isgen):
    daughters, mothers, associated = [], [], []
    for line in lines:
      id, status, mother1, mother2 = (int(_) for _ in line.split()[0:4])
      if (1 <= abs(id) <= 6 or abs(id) == 21) and not isgen:
        line = line.replace(str(id), "0", 1)  #replace the first instance of the jet id with 0, which means unknown jet
      if status == -1:
        mothers.append(line)
      if abs(id) in (11, 12, 13, 14, 15, 16) and status == 1:
        daughters.append(line)
      if abs(id) in (0, 1, 2, 3, 4, 5, 21) and status == 1:
        associated.append(line)

    if len(daughters) != 4:
      raise ValueError("Wrong number of daughters (expected {}, found {})\n\n".format(4, len(daughters))+"\n".join(lines))
    if cls.nassociatedparticles is not None and len(associated) != cls.nassociatedparticles:
      raise ValueError("Wrong number of associated particles (expected {}, found {})\n\n".format(cls.nassociatedparticles, len(associated))+"\n".join(lines))
    if len(mothers) != 2:
      raise ValueError("{} mothers in the event??\n\n".format(len(mothers))+"\n".join(lines))

    if not isgen: mothers = None
    return daughters, associated, mothers

  nassociatedparticles = None

class LHEFileBase(object, metaclass=abc.ABCMeta):
  """
  Simple class to iterate through an LHE file and calculate probabilities for each event
  Example usage:
  h1 = ROOT.TH1F("costheta1", "costheta1", 100, -1, 1)
  h2 = ROOT.TH1F("D_0minus", "D_0minus", 100, 0, 1)
  with LHEFile("filename.lhe") as f:
    for event in f:  #event becomes the mela object
      h1.Fill(event.computeDecayAngles().costheta1)
      event.ghz1 = 1
      p0plus = event.computeP()
      event.ghz4 = 1
      p0minus = event.computeP()
      h2.Fill(p0plus / (p0plus + p0minus))
  """

  __melas = {}

  def __init__(self, filename, *melaargs, **kwargs):
    self.isgen = kwargs.pop("isgen", True)
    reusemela = kwargs.pop("reusemela", False)
    gzip = kwargs.pop("gzip", False)
    if kwargs: raise ValueError("Unknown kwargs: " + ", ".join(kwargs))
    self.filename = filename
    if reusemela and melaargs in self.__melas:
      self.mela = self.__melas[melaargs]
    else:
      self.__melas[melaargs] = self.mela = Mela(*melaargs)

    openfunction = open
    if gzip: from gzip import GzipFile as openfunction
    self.f = openfunction(self.filename)
  def __enter__(self, *args, **kwargs):
    self.f.__enter__(*args, **kwargs)
    return self
  def __exit__(self, *args, **kwargs):
    return self.f.__exit__(*args, **kwargs)

  def __iter__(self):
    event = ""
    for linenumber, line in enumerate(self.f, start=1):
      if "<event>" not in line and not event:
        continue
      event += line
      if "</event>" in line:
        try:
          self._setInputEvent(event)
          yield self
          event = ""
        except GeneratorExit:
          raise
        except:
          print("On line", linenumber)
          raise
        finally:
          try:
            self.mela.resetInputEvent()
          except:
            pass

  def _setInputEvent(self, event):
    lheevent = self.lheeventclass(event, self.isgen)
    self.daughters = lheevent.daughters
    self.associated = lheevent.associated
    self.mothers = lheevent.mothers
    self.weight = lheevent.weight
    self.weights = lheevent.weights
    self.setInputEvent(*lheevent)

  @classmethod
  def _LHEclassattributes(cls):
    return "filename", "f", "mela", "isgen", "daughters", "mothers", "associated", "weight", "weights"

  def __getattr__(self, attr):
    if attr == "mela": raise RuntimeError("Something is wrong, trying to access mela before it's created")
    return getattr(self.mela, attr)
  def __setattr__(self, attr, value):
    if attr in self._LHEclassattributes():
      super(LHEFileBase, self).__setattr__(attr, value)
    else:
      setattr(self.mela, attr, value)

class LHEFile_Hwithdecay(LHEFileBase):
  lheeventclass = LHEEvent_Hwithdecay
class LHEFile_HwithdecayOnly(LHEFileBase):
  lheeventclass = LHEEvent_HwithdecayOnly
class LHEFile_StableHiggs(LHEFileBase):
  lheeventclass = LHEEvent_StableHiggs
class LHEFile_StableHiggsVH(LHEFileBase):
  lheeventclass = LHEEvent_StableHiggsVH
class LHEFile_StableHiggsZHHAWK(LHEFileBase):
  lheeventclass = LHEEvent_StableHiggsZHHAWK
class LHEFile_JHUGenVBFVH(LHEFileBase):
  lheeventclass = LHEEvent_JHUGenVBFVH
class LHEFile_JHUGenttH(LHEFileBase):
  lheeventclass = LHEEvent_JHUGenttH
class LHEFile_Offshell4l(LHEFileBase):
  lheeventclass = LHEEvent_Offshell4l
class LHEFile_VHHiggsdecay(LHEFileBase):
  lheeventclass = LHEEvent_VHHiggsdecay
  
if __name__ == '__main__':
  class TestLHEFiles(unittest.TestCase):
    @unittest.skipUnless(args.lhefile_hwithdecay, "needs --lhefile-hwithdecay argument")
    def testHwithDecay(self):
      with LHEFile_Hwithdecay(args.lhefile_hwithdecay) as f:
        for event, i in zip(f, list(range(10))):
          event.ghz1 = 1
          event.setProcess(TVar.SelfDefine_spin0, TVar.JHUGen, TVar.ZZINDEPENDENT)
          prob = event.computeP()
          self.assertNotEqual(prob, 0)
          print(prob, event.computeDecayAngles())

    @unittest.skipUnless(args.lhefile_jhugenvbfvh, "needs --lhefile-jhugenvbfvh argument")
    def testJHUGenVBFVH(self):
      with LHEFile_JHUGenVBFVH(args.lhefile_jhugenvbfvh, isgen=False) as f:
        for event, i in zip(f, list(range(10))):
          event.ghz1 = 1
          if any(11 <= abs(p.first) <= 16 for p in event.associated):
            if sum(p.first for p in event.associated) == 0:
              VHprocess = TVar.Lep_ZH
              event.setProcess(TVar.SelfDefine_spin0, TVar.JHUGen, TVar.Lep_ZH)
            else:
              VHprocess = TVar.Lep_WH
              event.setProcess(TVar.SelfDefine_spin0, TVar.JHUGen, TVar.Lep_WH)
          else:
            VHprocess = TVar.Had_ZH
            event.setProcess(TVar.SelfDefine_spin0, TVar.JHUGen, TVar.JJVBF)
          prob = event.computeProdP()
          self.assertNotEqual(prob, 0)
          print(prob, event.computeVBFAngles(), event.computeVHAngles(VHprocess))

    @unittest.skipUnless(args.lhefile_jhugentth, "needs --lhefile-jhugentth argument")
    def testJHUGenttH(self):
      with LHEFile_JHUGenttH(args.lhefile_jhugentth) as f:
        for event, i in zip(f, list(range(10))):
          pass

  unittest.main(argv=[sys.argv[0]]+args.unittest_args)
