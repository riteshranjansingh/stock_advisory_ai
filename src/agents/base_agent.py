"""
Base Agent Class
All trading agents inherit from this base class
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, date

class BaseAgent(ABC):
    """Base class for all trading agents"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"agents.{name}")
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        
        # Initialize agent
        self._initialize()
    
    def _initialize(self):
        """Initialize agent-specific settings"""
        self.logger.info(f"Initializing {self.name} agent")
    
    @abstractmethod
    def analyze(self, stock_symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis method - must be implemented by each agent
        
        Args:
            stock_symbol: Stock symbol to analyze
            data: Input data for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    def get_recommendation(self, stock_symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get trading recommendation for a stock
        
        Returns:
            {
                'action': 'BUY'/'SELL'/'HOLD',
                'confidence': float (0-1),
                'reasoning': str,
                'agent_name': str,
                'timestamp': datetime,
                'additional_data': dict
            }
        """
        try:
            # Perform analysis
            analysis_result = self.analyze(stock_symbol, data)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(analysis_result)
            
            # Add metadata
            recommendation.update({
                'agent_name': self.name,
                'timestamp': datetime.now(),
                'stock_symbol': stock_symbol
            })
            
            self.logger.info(f"Generated recommendation for {stock_symbol}: {recommendation['action']} (confidence: {recommendation['confidence']:.2f})")
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation for {stock_symbol}: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': f"Error in analysis: {str(e)}",
                'agent_name': self.name,
                'timestamp': datetime.now(),
                'stock_symbol': stock_symbol,
                'error': True
            }
    
    @abstractmethod
    def _generate_recommendation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading recommendation from analysis result"""
        pass
    
    def validate_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that required data fields are present"""
        try:
            for field in required_fields:
                if field not in data or data[field] is None:
                    self.logger.warning(f"Missing required field: {field}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Data validation error: {e}")
            return False
    
    def calculate_confidence(self, signals: List[float]) -> float:
        """Calculate overall confidence from multiple signals"""
        if not signals:
            return 0.0
        
        # Remove None values
        valid_signals = [s for s in signals if s is not None]
        
        if not valid_signals:
            return 0.0
        
        # Calculate weighted average (you can customize this logic)
        avg_signal = sum(valid_signals) / len(valid_signals)
        
        # Normalize to 0-1 range
        confidence = min(max(abs(avg_signal), 0.0), 1.0)
        
        return confidence
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            'name': self.name,
            'status': 'active',
            'confidence_threshold': self.confidence_threshold,
            'config': self.config,
            'last_updated': datetime.now()
        }
    
    def __str__(self):
        return f"{self.name}Agent"
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"