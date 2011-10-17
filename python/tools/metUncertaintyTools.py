import FWCore.ParameterSet.Config as cms

from FWCore.GuiBrowsers.ConfigToolBase import *
 
class RunMEtUncertainties(ConfigToolBase):

    """ Shift energy of electrons, photons, muons, tau-jets and other jets
    reconstructed in the event up/down,
    in order to estimate effect of energy scale uncertainties on MET
   """
    _label='runMEtUncertainties'
    _defaultParameters=dicttypes.SortedKeysDict()
    def __init__(self):
        ConfigToolBase.__init__(self)
        self.addParameter(self._defaultParameters, 'electronCollection', cms.InputTag('cleanPatElectrons'), 
	                  "Input electron collection", Type=cms.InputTag, acceptNoneValue=True)
	self.addParameter(self._defaultParameters, 'photonCollection', None, # CV: set to empty InputTag to avoid double-counting wrt. cleanPatElectrons collection 
	                  "Input photon collection", Type=cms.InputTag, acceptNoneValue=True)
	self.addParameter(self._defaultParameters, 'muonCollection', cms.InputTag('cleanPatMuons'), 
                          "Input muon collection", Type=cms.InputTag, acceptNoneValue=True)
	self.addParameter(self._defaultParameters, 'tauCollection', cms.InputTag('cleanPatTaus'), 
                          "Input tau collection", Type=cms.InputTag, acceptNoneValue=True)
	self.addParameter(self._defaultParameters, 'jetCollection', cms.InputTag('cleanPatJets'), 
                          "Input jet collection", Type=cms.InputTag)
	self.addParameter(self._defaultParameters, 'dRjetCleaning', 0.5, 
                          "Eta-phi distance for extra jet cleaning", Type=float)
        self.addParameter(self._defaultParameters, 'jetCorrLabel', "L3Absolute", 
                          "NOTE: use 'L3Absolute' for MC/'L2L3Residual' for Data", Type=str)
	self.addParameter(self._defaultParameters, 'doSmearJets', True, 
                          "Flag to enable/disable jet smearing to better match MC to Data", Type=bool)
	self.addParameter(self._defaultParameters, 'jetSmearFileName', 'PhysicsTools/PatUtils/data/pfJetResolutionMCtoDataCorrLUT.root', 
                          "Name of ROOT file containing histogram with jet smearing factors", Type=str) 
        self.addParameter(self._defaultParameters, 'jetSmearHistogram', 'pfJetResolutionMCtoDataCorrLUT', 
                          "Name of histogram with jet smearing factors", Type=str) 
	self.addParameter(self._defaultParameters, 'doCorrType1p2MEt', False, 
	                  "Flag to enable/disable estimation for Type 1+2 corrected MET", Type=bool)
	self.addParameter(self._defaultParameters, 'pfCandCollection', cms.InputTag('particleFlow'), 
                          "Input PFCandidate collection", Type=cms.InputTag)	
	self.addParameter(self._defaultParameters, 'jetCorrPayloadName', 'AK5PF', 
                          "Use AK5PF for PFJets, AK5Calo for CaloJets", Type=str)
	self.addParameter(self._defaultParameters, 'varyByNsigmas', 1.0, 
                          "Number of standard deviations by which energies are varied", Type=float)
        self._parameters=copy.deepcopy(self._defaultParameters)
        self._comment = ""
        
    def getDefaultParameters(self):
        return self._defaultParameters

    def _addModuleToSequence(self, process, module, moduleName_parts, sequence):

        if not len(moduleName_parts) > 0:
            raise ValueError("Empty list !!")

        moduleName = ""

        lastPart = None
        for part in moduleName_parts:
            if part is None or part == "":
                continue

            part = part.replace("selected", "")
            part = part.replace("clean",    "")

            if lastPart is None:
                moduleName += part[0].lower() + part[1:]
                lastPart = part
            else:
                if lastPart[-1].islower() or lastPart[-1].isdigit():
                    moduleName += part[0].capitalize() + part[1:]
                else:
                    moduleName += part[0].lower() + part[1:]
                lastPart = part    

        setattr(process, moduleName, module)

        sequence += module
 
        return moduleName

    def _propagateMEtUncertainties(self, process, particleCollection, particleType, particleCollectionEnUp, particleCollectionEnDown, correctedMET, sequence):

        moduleMETtype1p2CorrEnUp = cms.EDProducer("ShiftedParticleMETcorrInputProducer",
            srcOriginal = cms.InputTag(particleCollection),
            srcShifted = cms.InputTag(particleCollectionEnUp)                                           
        )
        moduleMETtype1p2CorrEnUpName = "patPFJetMETtype1p2Corr%sEnUp" % particleType
        setattr(process, moduleMETtype1p2CorrEnUpName, moduleMETtype1p2CorrEnUp)
        sequence += moduleMETtype1p2CorrEnUp
        moduleType1CorrectedMETenUp = correctedMET.clone(
            src = cms.InputTag(correctedMET.label()),
            srcType1Corrections = cms.VInputTag(
                cms.InputTag(moduleMETtype1p2CorrEnUpName)
            )
        )
        moduleType1CorrectedMETenUpName = "%s%sEnUp" % (correctedMET.label(), particleType)
        setattr(process, moduleType1CorrectedMETenUpName, moduleType1CorrectedMETenUp)
        sequence += moduleType1CorrectedMETenUp

        moduleMETtype1p2CorrEnDown = moduleMETtype1p2CorrEnUp.clone(
            srcShifted = cms.InputTag(particleCollectionEnDown)                                           
        )
        moduleMETtype1p2CorrEnDownName = "patPFJetMETtype1p2Corr%sEnDown" % particleType
        setattr(process, moduleMETtype1p2CorrEnDownName, moduleMETtype1p2CorrEnDown)
        sequence += moduleMETtype1p2CorrEnDown
        moduleType1CorrectedMETenDown = moduleType1CorrectedMETenUp.clone(
            srcType1Corrections = cms.VInputTag(
                cms.InputTag(moduleMETtype1p2CorrEnDownName)
            )
        )
        moduleType1CorrectedMETenDownName = "%s%sEnDown" % (correctedMET.label(), particleType)
        setattr(process, moduleType1CorrectedMETenDownName, moduleType1CorrectedMETenDown)
        sequence += moduleType1CorrectedMETenDown

    def __call__(self,process,
                 electronCollection = None,
                 photonCollection   = None,
                 muonCollection     = None,
                 tauCollection      = None,
                 jetCollection      = None,
                 dRjetCleaning      = None,
                 jetCorrLabel       = None,
                 doSmearJets        = None,
                 jetSmearFileName   = None,
                 jetSmearHistogram  = None,
                 pfCandCollection   = None,
                 jetCorrPayloadName = None,
                 varyByNsigmas      = None):
        if electronCollection is None:
            electronCollection = self._defaultParameters['electronCollection'].value
        if photonCollection is None:
            photonCollection = self._defaultParameters['photonCollection'].value
        if muonCollection is None:
            muonCollection = self._defaultParameters['muonCollection'].value
        if tauCollection is None:
            tauCollection = self._defaultParameters['tauCollection'].value    
        if jetCollection is None:
            jetCollection = self._defaultParameters['jetCollection'].value
        if jetCorrLabel is None:
            jetCorrLabel = self._defaultParameters['jetCorrLabel'].value
        if dRjetCleaning is None:
            dRjetCleaning = self._defaultParameters['dRjetCleaning'].value
        if doSmearJets is None:
            doSmearJets = self._defaultParameters['doSmearJets'].value
        if jetSmearFileName is None:
            jetSmearFileName = self._defaultParameters['jetSmearFileName'].value
        if jetSmearHistogram is None:
            jetSmearHistogram = self._defaultParameters['jetSmearHistogram'].value    
        if pfCandCollection is None:
            pfCandCollection = self._defaultParameters['pfCandCollection'].value
        if jetCorrPayloadName is None:
            jetCorrPayloadName = self._defaultParameters['jetCorrPayloadName'].value
        if varyByNsigmas is None:
            varyByNsigmas = self._defaultParameters['varyByNsigmas'].value   

        self.setParameter('electronCollection', electronCollection)
        self.setParameter('photonCollection', photonCollection)
        self.setParameter('muonCollection', muonCollection)
        self.setParameter('tauCollection', tauCollection)
        self.setParameter('jetCollection', jetCollection)
        self.setParameter('jetCorrLabel', jetCorrLabel)
        self.setParameter('dRjetCleaning', dRjetCleaning)
        self.setParameter('doSmearJets', doSmearJets)
        self.setParameter('jetSmearFileName', jetSmearFileName)
        self.setParameter('jetSmearHistogram', jetSmearHistogram)
        self.setParameter('pfCandCollection', pfCandCollection)
        self.setParameter('jetCorrPayloadName', jetCorrPayloadName)
        self.setParameter('varyByNsigmas', varyByNsigmas)
  
        self.apply(process) 
        
    def toolCode(self, process):        
        electronCollection = self._parameters['electronCollection'].value
        photonCollection = self._parameters['photonCollection'].value
        muonCollection = self._parameters['muonCollection'].value
        tauCollection = self._parameters['tauCollection'].value
        jetCollection = self._parameters['jetCollection'].value
        jetCorrLabel = self._parameters['jetCorrLabel'].value
        dRjetCleaning =  self._parameters['dRjetCleaning'].value
        doSmearJets = self._parameters['doSmearJets'].value
        jetSmearFileName = self._parameters['jetSmearFileName'].value
        jetSmearHistogram = self._parameters['jetSmearHistogram'].value
        pfCandCollection = self._parameters['pfCandCollection'].value
        jetCorrPayloadName = self._parameters['jetCorrPayloadName'].value
        varyByNsigmas = self._parameters['varyByNsigmas'].value

        process.metUncertaintySequence = cms.Sequence()

        # produce collection of jets not overlapping with reconstructed
        # electrons/photons, muons and tau-jet candidates
        collectionsForJetCleaning = []
        for collection in [ electronCollection, photonCollection, muonCollection, tauCollection ]:
            if collection is not None:
                collectionsForJetCleaning.append(collection)
        jetsAntiOverlapWithLeptonsForMEtUncertainty = cms.EDFilter("PATJetAntiOverlapSelector",
            src = jetCollection,                                                         
            srcNotToBeFiltered = cms.VInputTag(collectionsForJetCleaning),
            dRmin = cms.double(dRjetCleaning),
            filter = cms.bool(False)                                           
        )
        lastJetCollection = \
          self._addModuleToSequence(process, jetsAntiOverlapWithLeptonsForMEtUncertainty, [ jetCollection.value(), "AntiOverlapWithLeptonsForMEtUncertainty" ], process.metUncertaintySequence) 

        # smear jet energies to account for difference in jet resolutions between MC and Data
        # (cf. JME-10-014 PAS)
        if doSmearJets:
            smearedJets = cms.EDProducer("SmearedPATJetProducer",
                src = cms.InputTag(lastJetCollection),
                inputFileName = cms.FileInPath(jetSmearFileName),
                lutName = cms.string(jetSmearHistogram)
            )
            lastJetCollection = \
              self._addModuleToSequence(process, smearedJets, [ "smeared", jetCollection.value() ], process.metUncertaintySequence) 

        #--------------------------------------------------------------------------------------------
        # produce collection of jets shifted up/down in energy    
        #--------------------------------------------------------------------------------------------     
 
        jetsEnUp = cms.EDProducer("ShiftedPATJetProducer",
            src = cms.InputTag(lastJetCollection),
            jetCorrPayloadName = cms.string(jetCorrPayloadName),
            jetCorrUncertaintyTag = cms.string('Uncertainty'),
            shiftBy = cms.double(+1.*varyByNsigmas)
        )
        jetCollectionEnUp = \
          self._addModuleToSequence(process, jetsEnUp, [ "shifted", jetCollection.value(), "EnUp" ], process.metUncertaintySequence) 
        jetsEnDown = jetsEnUp.clone(
            shiftBy = cms.double(-1.*varyByNsigmas)
        )
        jetCollectionEnDown = \
          self._addModuleToSequence(process, jetsEnDown, [ "shifted", jetCollection.value(), "EnDown" ], process.metUncertaintySequence) 

        #--------------------------------------------------------------------------------------------
        # produce collection of electrons shifted up/down in energy
        #--------------------------------------------------------------------------------------------

        electronCollectionEnUp = None
        electronCollectionEnDown = None
        if electronCollection is not None:
            electronsEnUp = cms.EDProducer("ShiftedPATElectronProducer",
                src = electronCollection,
                binning = cms.VPSet(
                    cms.PSet(
                        binSelection = cms.string('isEB'),
                        binUncertainty = cms.double(0.01)
                    ),
                    cms.PSet(
                        binSelection = cms.string('!isEB'),
                        binUncertainty = cms.double(0.025)
                    ),
                ),      
                shiftBy = cms.double(+1.*varyByNsigmas)
            )
            electronCollectionEnUp = \
              self._addModuleToSequence(process, electronsEnUp, [ "shifted", electronCollection.value(), "EnUp" ], process.metUncertaintySequence) 
            electronsEnDown = electronsEnUp.clone(
                shiftBy = cms.double(-1.*varyByNsigmas)
            )
            electronCollectionEnDown = \
              self._addModuleToSequence(process, electronsEnDown, [ "shifted", electronCollection.value(), "EnDown" ], process.metUncertaintySequence) 

        #--------------------------------------------------------------------------------------------
        # produce collection of (high Pt) photon candidates shifted up/down in energy
        #--------------------------------------------------------------------------------------------    

        photonCollectionEnUp = None
        photonCollectionEnDown = None    
        if photonCollection is not None:
            photonsEnUp = cms.EDProducer("ShiftedPATPhotonProducer",
                src = photonCollection,
                binning = cms.VPSet(
                    cms.PSet(
                        binSelection = cms.string('isEB = true'),
                        binUncertainty = cms.double(0.01)
                    ),
                    cms.PSet(
                        binSelection = cms.string('isEB = false'),
                        binUncertainty = cms.double(0.025)
                    ),
                ),                         
                shiftBy = cms.double(+1.*varyByNsigmas)
            )
            photonCollectionEnUp = \
              self._addModuleToSequence(process, photonsEnUp, [ "shifted", photonCollection.value(), "EnUp" ], process.metUncertaintySequence) 
            photonsEnDown = photonsEnUp.clone(
                shiftBy = cms.double(-1.*varyByNsigmas)
            )
            photonCollectionEnDown = \
              self._addModuleToSequence(process, photonsEnDown, [ "shifted", photonCollection.value(), "EnDown" ], process.metUncertaintySequence) 

        #--------------------------------------------------------------------------------------------
        # produce collection of muons shifted up/down in energy/momentum  
        #--------------------------------------------------------------------------------------------

        muonCollectionEnUp = None
        muonCollectionEnDown = None   
        if muonCollection is not None:
            muonsEnUp = cms.EDProducer("ShiftedPATMuonProducer",
                src = muonCollection,
                uncertainty = cms.double(0.01),
                shiftBy = cms.double(+1.*varyByNsigmas)
            )
            muonCollectionEnUp = \
              self._addModuleToSequence(process, muonsEnUp, [ "shifted", muonCollection.value(), "EnUp" ], process.metUncertaintySequence) 
            muonsEnDown = muonsEnUp.clone(
                shiftBy = cms.double(-1.*varyByNsigmas)
            )
            muonCollectionEnDown = \
              self._addModuleToSequence(process, muonsEnDown, [ "shifted", muonCollection.value(), "EnDown" ], process.metUncertaintySequence) 

        #--------------------------------------------------------------------------------------------
        # produce collection of tau-jets shifted up/down in energy
        #--------------------------------------------------------------------------------------------     

        tauCollectionEnUp = None
        tauCollectionEnDown = None 
        if tauCollection is not None:
            tausEnUp = cms.EDProducer("ShiftedPATTauProducer",
                src = tauCollection,
                uncertainty = cms.double(0.03),                      
                shiftBy = cms.double(+1.*varyByNsigmas)
            )
            tauCollectionEnUp = \
              self._addModuleToSequence(process, tausEnUp, [ "shifted", tauCollection.value(), "EnUp" ], process.metUncertaintySequence) 
            tausEnDown = tausEnUp.clone(
                shiftBy = cms.double(-1.*varyByNsigmas)
            )
            tauCollectionEnDown = \
              self._addModuleToSequence(process, tausEnDown, [ "shifted", tauCollection.value(), "EnDown" ], process.metUncertaintySequence)     

        #--------------------------------------------------------------------------------------------    
        # propagate shifted jet energies to MET
        #--------------------------------------------------------------------------------------------

        process.load("PhysicsTools.PatUtils.patPFMETCorrections_cff")
        process.selectedPatJetsForMETtype1p2Corr.src = jetCollection
        process.selectedPatJetsForMETtype2Corr.src = jetCollection
        process.pfCandsNotInJet.bottomCollection = pfCandCollection
        process.metUncertaintySequence += process.producePatPFMETCorrections

        # split jet collections into |jetEta| < 4.7 and |jetEta| > 4.7 parts
        #
        # NOTE: splitting of pat::Jets collections needs to be done
        #       in order to work around problem with CMSSW_4_2_x JEC factors at high eta,
        #       reported in
        #         https://hypernews.cern.ch/HyperNews/CMS/get/jes/270.html
        #         https://hypernews.cern.ch/HyperNews/CMS/get/JetMET/1259/1.html )
        #
        process.selectedPatJetsForMETtype1p2CorrEnUp = process.selectedPatJetsForMETtype1p2Corr.clone(
            src = cms.InputTag(jetCollectionEnUp)
        )
        process.metUncertaintySequence += process.selectedPatJetsForMETtype1p2CorrEnUp
        process.selectedPatJetsForMETtype2CorrEnUp = process.selectedPatJetsForMETtype2Corr.clone(
            src = cms.InputTag(jetCollectionEnUp)
        )
        process.metUncertaintySequence += process.selectedPatJetsForMETtype2CorrEnUp
        process.selectedPatJetsForMETtype1p2CorrEnDown = process.selectedPatJetsForMETtype1p2CorrEnUp.clone(
            src = cms.InputTag(jetCollectionEnDown)
        )
        process.metUncertaintySequence += process.selectedPatJetsForMETtype1p2CorrEnDown
        process.selectedPatJetsForMETtype2CorrEnDown = process.selectedPatJetsForMETtype2CorrEnUp.clone(
            src = cms.InputTag(jetCollectionEnDown)
        )
        process.metUncertaintySequence += process.selectedPatJetsForMETtype2CorrEnDown

        # produce Type 1 + 2 MET corrections for shifted jet collections
        process.patPFJetMETtype1p2CorrEnUp = process.patPFJetMETtype1p2Corr.clone(
            src = cms.InputTag(process.selectedPatJetsForMETtype1p2CorrEnUp.label()),
            jetCorrLabel = cms.string(jetCorrLabel)
        )
        process.metUncertaintySequence += process.patPFJetMETtype1p2CorrEnUp
        process.patPFJetMETtype1p2CorrEnDown = process.patPFJetMETtype1p2CorrEnUp.clone(
            src = cms.InputTag(process.selectedPatJetsForMETtype1p2CorrEnDown.label())
        )
        process.metUncertaintySequence += process.patPFJetMETtype1p2CorrEnDown

        process.patType1CorrectedPFMetJetEnUp = process.patType1CorrectedPFMet.clone(
            src = cms.InputTag('patType1CorrectedPFMet'),
            srcType1Corrections = cms.VInputTag(
                cms.InputTag('patPFJetMETtype1p2CorrEnUp', 'type1')
            )
        )
        process.metUncertaintySequence += process.patType1CorrectedPFMetJetEnUp
        process.patType1CorrectedPFMetJetEnDown = process.patType1CorrectedPFMetJetEnUp.clone(
            srcType1Corrections = cms.VInputTag(
                cms.InputTag('patPFJetMETtype1p2CorrEnDown', 'type1')
            )
        )
        process.metUncertaintySequence += process.patType1CorrectedPFMetJetEnDown

        process.patType1p2CorrectedPFMetJetEnUp = process.patType1p2CorrectedPFMet.clone(
            src = cms.InputTag('patType1p2CorrectedPFMet'),
            srcType1Corrections = cms.VInputTag(
                cms.InputTag('patPFJetMETtype1p2CorrEnUp', 'type1')
            )
        )
        process.metUncertaintySequence += process.patType1p2CorrectedPFMetJetEnUp
        process.patType1p2CorrectedPFMetJetEnDown = process.patType1p2CorrectedPFMetJetEnUp.clone(
            srcType1Corrections = cms.VInputTag(
                cms.InputTag('patPFJetMETtype1p2CorrEnDown', 'type1')
            )
        )
        process.metUncertaintySequence += process.patType1p2CorrectedPFMetJetEnDown

        #--------------------------------------------------------------------------------------------
        # shift "unclustered energy" (PFJets of Pt < 10 GeV plus PFCandidates not within jets)
        # and propagate effect of shift to (Type 1 as well as Type 1 + 2 corrected) MET
        #--------------------------------------------------------------------------------------------

        unclEnMETcorrections = [
            [ 'pfCandMETcorr', [ '' ] ],
            [ 'patPFJetMETtype1p2Corr', [ 'type2', 'offset' ] ],
            [ 'patPFJetMETtype2Corr', [ 'type2' ] ],
        ]
        unclEnMETcorrectionsUp = []
        unclEnMETcorrectionsDown = []
        for srcUnclEnMETcorr in unclEnMETcorrections:
            moduleUnclEnMETcorrUp = cms.EDProducer("ShiftedMETcorrInputProducer",
                src = cms.VInputTag(
                    [ cms.InputTag(srcUnclEnMETcorr[0], instanceLabel) for instanceLabel in srcUnclEnMETcorr[1] ]
                ),
                uncertainty = cms.double(0.10),
                shiftBy = cms.double(+1.*varyByNsigmas)
            )
            moduleUnclEnMETcorrUpName = "%sUnclusteredEnUp" % srcUnclEnMETcorr[0]
            setattr(process, moduleUnclEnMETcorrUpName, moduleUnclEnMETcorrUp)
            process.metUncertaintySequence += moduleUnclEnMETcorrUp
            unclEnMETcorrectionsUp.extend([ cms.InputTag(moduleUnclEnMETcorrUpName, instanceLabel) for instanceLabel in srcUnclEnMETcorr[1] ] )
            moduleUnclEnMETcorrDown = moduleUnclEnMETcorrUp.clone(
                shiftBy = cms.double(-1.*varyByNsigmas)
            )
            moduleUnclEnMETcorrDownName = "%sUnclusteredEnDown" % srcUnclEnMETcorr[0]
            setattr(process, moduleUnclEnMETcorrDownName, moduleUnclEnMETcorrDown)
            process.metUncertaintySequence += moduleUnclEnMETcorrDown
            unclEnMETcorrectionsDown.extend([ cms.InputTag(moduleUnclEnMETcorrDownName, instanceLabel) for instanceLabel in srcUnclEnMETcorr[1] ] )
            
        process.patType1CorrectedPFMetUnclusteredEnUp = process.patType1CorrectedPFMet.clone(
            src = cms.InputTag('patType1CorrectedPFMet'),
            srcType1Corrections = cms.VInputTag(unclEnMETcorrectionsUp)
        )
        process.metUncertaintySequence += process.patType1CorrectedPFMetUnclusteredEnUp
        process.patType1CorrectedPFMetUnclusteredEnDown = process.patType1CorrectedPFMetUnclusteredEnUp.clone(
            srcType1Corrections = cms.VInputTag(unclEnMETcorrectionsDown)
        )
        process.metUncertaintySequence += process.patType1CorrectedPFMetUnclusteredEnDown    

        process.patType1p2CorrectedPFMetUnclusteredEnUp = process.patType1p2CorrectedPFMet.clone(
            src = cms.InputTag('patType1p2CorrectedPFMet'),
            srcType1Corrections = cms.VInputTag(unclEnMETcorrectionsUp)
        )
        process.metUncertaintySequence += process.patType1p2CorrectedPFMetUnclusteredEnUp
        process.patType1p2CorrectedPFMetUnclusteredEnDown = process.patType1p2CorrectedPFMetUnclusteredEnUp.clone(
            srcType1Corrections = cms.VInputTag(unclEnMETcorrectionsDown)
        )
        process.metUncertaintySequence += process.patType1p2CorrectedPFMetUnclusteredEnDown

        #--------------------------------------------------------------------------------------------    
        # propagate shifted electron/photon, muon and tau-jet energies to MET
        #--------------------------------------------------------------------------------------------

        for corrMET in [ process.patType1CorrectedPFMet, 
                         process.patType1p2CorrectedPFMet ]:
            
            if electronCollection is not None:
                self._propagateMEtUncertainties(process, electronCollection.value(), "Electron", 
                                                electronCollectionEnUp, electronCollectionEnDown, corrMET, process.metUncertaintySequence)

            if photonCollection is not None:
                self._propagateMEtUncertainties(process, photonCollection.value(), "Photon", 
                                                photonCollectionEnUp, photonCollectionEnDown, corrMET, process.metUncertaintySequence)
                
            if muonCollection is not None:
                self._propagateMEtUncertainties(process, muonCollection.value(), "Muon", 
                                                muonCollectionEnUp, muonCollectionEnDown, corrMET, process.metUncertaintySequence)

            if tauCollection is not None:
                self._propagateMEtUncertainties(process, tauCollection.value(), "Tau", 
                                                tauCollectionEnUp, tauCollectionEnDown, corrMET, process.metUncertaintySequence)

        if not hasattr(process, "patDefaultSequence"):
            raise ValueError("PAT default sequence is not defined !!")
        process.patDefaultSequence += process.metUncertaintySequence 
       
runMEtUncertainties=RunMEtUncertainties()