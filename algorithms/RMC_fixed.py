"""
RMC_fixed.py - Wrapper for RecursiveMetaCognitionEngine
Provides the global instance used by the cognitive CLI
"""

from RMC import RecursiveMetaCognitionEngine

# Global instance
rmc_engine = RecursiveMetaCognitionEngine()

def get_rmc_engine():
    """Get the global RMC engine instance"""
    return rmc_engine
