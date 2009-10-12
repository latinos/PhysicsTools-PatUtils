#ifndef PhysicsTools_PatUtils_interface_JetIDSelectionFunctor_h
#define PhysicsTools_PatUtils_interface_JetIDSelectionFunctor_h


/**
  \class    JetIDSelectionFunctor JetIDSelectionFunctor.h "PhysicsTools/Utilities/interface/JetIDSelectionFunctor.h"
  \brief    Jet selector for pat::Jets

  Selector functor for pat::Jets that implements quality cuts based on
  studies of noise patterns. 

  Please see https://twiki.cern.ch/twiki/bin/view/CMS/SWGuidePATSelectors
  for a general overview of the selectors. 

  \author Salvatore Rappoccio
  \version  $Id: JetIDSelectionFunctor.h,v 1.1.2.3 2009/10/11 15:16:28 srappocc Exp $
*/




#include "DataFormats/PatCandidates/interface/Jet.h"
#include "FWCore/MessageLogger/interface/MessageLogger.h"

#include "PhysicsTools/Utilities/interface/Selector.h"

#include <TMath.h>
class JetIDSelectionFunctor : public Selector<pat::Jet>  {

 public: // interface

  enum Version_t { CRAFT08, N_VERSIONS };
  enum Quality_t { LOOSE, TIGHT, N_QUALITY};
  

 JetIDSelectionFunctor( Version_t version, Quality_t quality ) :
  version_(version), quality_(quality)
  {
    push_back("LOOSE_fHPD");
    push_back("LOOSE_N90Hits");
    push_back("LOOSE_EMF");

    push_back("TIGHT_fHPD");
    push_back("TIGHT_EMF");

    // all on by default
    set("LOOSE_fHPD");
    set("LOOSE_N90Hits");
    set("LOOSE_EMF");
    set("TIGHT_fHPD");
    set("TIGHT_EMF");
    
  }

  // Allow for multiple definitions of the cuts. 
  bool operator()( const pat::Jet & jet, std::strbitset & ret )  
  {
    if ( version_ == CRAFT08 ) return craft08Cuts( jet, ret );
    else {
      return false;
    }
  }

  // cuts based on craft 08 analysis. 
  bool craft08Cuts( const pat::Jet & jet, std::strbitset & ret) 
  {

    if ( quality_ == LOOSE || quality_ == TIGHT ) {
      // initialize return value
      double abs_eta = TMath::Abs( jet.eta() );
      double corrPt = jet.correctedP4( pat::JetCorrFactors::L3 ).Pt();

      // loose fhpd cut
      if ( ignoreCut("LOOSE_fHPD")    || jet.jetID().fHPD < 0.98 ) passCut( ret, "LOOSE_fHPD");
      // loose n90 hits cut
      if ( ignoreCut("LOOSE_N90Hits") || jet.jetID().n90Hits > 1 ) passCut( ret, "LOOSE_N90Hits");

      // loose EMF Cut
      bool emf_loose = true;
      if( abs_eta <= 2.55 ) { // HBHE
	if( jet.emEnergyFraction() <= 0.01 ) emf_loose = false;
      } else {                // HF
	if( jet.emEnergyFraction() <= -0.9 ) emf_loose = false;
	if( corrPt > 80 && jet.emEnergyFraction() >= 1 ) emf_loose = false;
      }
      if ( ignoreCut("LOOSE_EMF") || emf_loose ) passCut(ret, "LOOSE_EMF");
 
      if ( quality_ == TIGHT ) {
	// tight fhpd cut
	bool tight_fhpd = true;
	if ( jet.pt() >= 25 && jet.jetID().fHPD >= 0.95 ) tight_fhpd = false;
	if ( ignoreCut("TIGHT_fHPD") || tight_fhpd ) passCut(ret, "TIGHT_fHPD");
	
	// tight emf cut
	bool tight_emf = true;
	if( abs_eta >= 1 && corrPt >= 80 && jet.emEnergyFraction() >= 1 ) tight_emf = false; // outside HB	  
	if( abs_eta >= 2.55 ) { // outside HBHE
	  if( jet.emEnergyFraction() <= -0.3 ) tight_emf = false;
	  if( abs_eta < 3.25 ) { // HE-HF transition region
	    if( corrPt >= 50 && jet.emEnergyFraction() <= -0.2 ) tight_emf = false;
	    if( corrPt >= 80 && jet.emEnergyFraction() <= -0.1 ) tight_emf = false;	
	    if( corrPt >= 340 && jet.emEnergyFraction() >= 0.95 ) tight_emf = false;
	  } else { // HF
	    if( jet.emEnergyFraction() >= 0.9 ) tight_emf = false;
	    if( corrPt >= 50 && jet.emEnergyFraction() <= -0.2 ) tight_emf = false;
	    if( corrPt >= 50 && jet.emEnergyFraction() >= 0.8 ) tight_emf = false;
	    if( corrPt >= 130 && jet.emEnergyFraction() <= -0.1 ) tight_emf = false;
	    if( corrPt >= 130 && jet.emEnergyFraction() >= 0.7 ) tight_emf = false;
	
	  } // end if HF
	}// end if outside HBHE
	if ( ignoreCut("TIGHT_EMF") || tight_emf ) passCut(ret, "TIGHT_EMF");
      }    
    }

    return (bool)ret;
  }
  
 private: // member variables
  
  Version_t version_;
  Quality_t quality_;
  
};

#endif
