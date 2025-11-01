"""
🗺️ Dubai Real Estate Knowledge Base
Communities, price ranges, amenities, market insights, and location intelligence
"""

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

# ==========================================
# ENUMS & DATA MODELS
# ==========================================

class CommunityTier(str, Enum):
    ULTRA_LUXURY = "ultra_luxury"
    LUXURY = "luxury"
    PREMIUM = "premium"
    AFFORDABLE = "affordable"

class PropertyAvailability(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SOLD_OUT = "sold_out"

class Community(BaseModel):
    name: str
    tier: CommunityTier
    price_range_min: int
    price_range_max: int
    property_types: List[str]
    amenities: List[str]
    nearby_landmarks: List[str]
    coordinates: Optional[Tuple[float, float]] = None
    developer: Optional[str] = None
    handover_year: Optional[int] = None
    district: Optional[str] = None
    rental_yield: Optional[str] = None
    investment_score: Optional[int] = None  # 1-10
    family_friendly: bool = True
    beach_access: bool = False
    metro_access: bool = False

class MarketInsight(BaseModel):
    community: str
    avg_price_per_sqft: Optional[int] = None
    price_trend: str = "stable"  # rising, stable, declining
    demand_level: str = "medium"  # high, medium, low
    rental_yield: str = "5-7%"
    investment_potential: str = "medium"  # high, medium, low
    best_for: List[str] = []
    updated_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.updated_at:
            self.updated_at = datetime.now()

# ==========================================
# DUBAI KNOWLEDGE BASE
# ==========================================

class DubaiKnowledge:
    """Complete Dubai real estate knowledge base"""
    
    def __init__(self):
        self.communities: Dict[str, Community] = self._initialize_communities()
        self.aliases = self._initialize_aliases()
        self.market_insights = self._initialize_market_insights()
        
        # Districts mapping
        self.districts = {
            "Beachfront": ["Palm Jumeirah", "Jumeirah Beach Residence", "Dubai Marina"],
            "Downtown": ["Downtown Dubai", "Business Bay", "DIFC"],
            "Family Communities": ["Arabian Ranches", "Dubai Hills Estate", "Jumeirah Village Circle"],
            "Affordable": ["Dubai Silicon Oasis", "Discovery Gardens", "International City"],
            "Commercial": ["Business Bay", "DIFC", "Dubai Internet City"]
        }
    
    def _initialize_communities(self) -> Dict[str, Community]:
        """Initialize comprehensive Dubai communities database"""
        
        return {
            # ==========================================
            # ULTRA LUXURY COMMUNITIES
            # ==========================================
            "Palm Jumeirah": Community(
                name="Palm Jumeirah",
                tier=CommunityTier.ULTRA_LUXURY,
                price_range_min=5_000_000,
                price_range_max=100_000_000,
                property_types=["villa", "apartment", "penthouse"],
                amenities=[
                    "Private beach", "5-star hotels", "Fine dining", 
                    "Water sports", "Yacht berths", "Beach clubs",
                    "Spa & wellness", "Shopping malls"
                ],
                nearby_landmarks=[
                    "Atlantis The Palm", "Nakheel Mall", "Palm West Beach",
                    "The Pointe", "Aquaventure Waterpark"
                ],
                coordinates=(25.1124, 55.1390),
                developer="Nakheel",
                handover_year=2009,
                district="Beachfront",
                rental_yield="4-6%",
                investment_score=9,
                family_friendly=True,
                beach_access=True,
                metro_access=False
            ),
            
            "Emirates Hills": Community(
                name="Emirates Hills",
                tier=CommunityTier.ULTRA_LUXURY,
                price_range_min=15_000_000,
                price_range_max=80_000_000,
                property_types=["villa", "mansion"],
                amenities=[
                    "Championship golf course", "Private lakes", 
                    "24/7 security", "Landscaped gardens", "Gated community",
                    "Country club", "Tennis courts"
                ],
                nearby_landmarks=[
                    "Emirates Golf Club", "Dubai Marina", "Mall of the Emirates"
                ],
                coordinates=(25.0525, 55.1776),
                developer="Emaar",
                handover_year=2003,
                district="Luxury Villas",
                rental_yield="3-5%",
                investment_score=10,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "Jumeirah Bay Island": Community(
                name="Jumeirah Bay Island",
                tier=CommunityTier.ULTRA_LUXURY,
                price_range_min=25_000_000,
                price_range_max=150_000_000,
                property_types=["villa", "mansion"],
                amenities=[
                    "Private island", "Beach club", "Marina berths",
                    "Concierge service", "Landscaped parks", "Private beach",
                    "Gourmet dining", "Spa facilities"
                ],
                nearby_landmarks=[
                    "Bulgari Resort & Residences", "Jumeirah Beach", "City Walk"
                ],
                coordinates=(25.2284, 55.2479),
                developer="Meraas",
                handover_year=2017,
                district="Beachfront",
                rental_yield="3-4%",
                investment_score=9,
                family_friendly=False,
                beach_access=True,
                metro_access=False
            ),
            
            "Al Barari": Community(
                name="Al Barari",
                tier=CommunityTier.ULTRA_LUXURY,
                price_range_min=10_000_000,
                price_range_max=50_000_000,
                property_types=["villa"],
                amenities=[
                    "Botanical gardens", "Organic farm", "Spa", "Restaurants",
                    "Kids club", "Swimming pools", "Wellness center", "Eco-friendly"
                ],
                nearby_landmarks=[
                    "Dubai Polo & Equestrian Club", "Arabian Ranches", "Motor City"
                ],
                coordinates=(25.1187, 55.2344),
                developer="Al Barari Developers",
                handover_year=2010,
                district="Green Community",
                rental_yield="4-6%",
                investment_score=8,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            # ==========================================
            # LUXURY COMMUNITIES
            # ==========================================
            "Dubai Marina": Community(
                name="Dubai Marina",
                tier=CommunityTier.LUXURY,
                price_range_min=1_500_000,
                price_range_max=20_000_000,
                property_types=["apartment", "penthouse"],
                amenities=[
                    "Marina walk", "Waterfront dining", "Metro station",
                    "Beach access", "Yacht club", "Shopping malls",
                    "Parks", "Jogging tracks"
                ],
                nearby_landmarks=[
                    "JBR Beach", "Marina Mall", "Dubai Marina Mall",
                    "Ain Dubai", "The Beach"
                ],
                coordinates=(25.0772, 55.1386),
                developer="Multiple",
                handover_year=2003,
                district="Beachfront",
                rental_yield="6-8%",
                investment_score=8,
                family_friendly=True,
                beach_access=True,
                metro_access=True
            ),
            
            "Downtown Dubai": Community(
                name="Downtown Dubai",
                tier=CommunityTier.LUXURY,
                price_range_min=2_000_000,
                price_range_max=30_000_000,
                property_types=["apartment", "penthouse"],
                amenities=[
                    "Burj Khalifa", "Dubai Mall", "Dubai Opera",
                    "Dubai Fountain", "Restaurants", "Metro",
                    "Souk Al Bahar", "Parks"
                ],
                nearby_landmarks=[
                    "Burj Khalifa", "Dubai Mall", "Dubai Opera",
                    "Souk Al Bahar", "Dubai Fountain"
                ],
                coordinates=(25.1972, 55.2744),
                developer="Emaar",
                handover_year=2004,
                district="Downtown",
                rental_yield="5-7%",
                investment_score=9,
                family_friendly=True,
                beach_access=False,
                metro_access=True
            ),
            
            "Business Bay": Community(
                name="Business Bay",
                tier=CommunityTier.LUXURY,
                price_range_min=1_200_000,
                price_range_max=15_000_000,
                property_types=["apartment", "office", "penthouse"],
                amenities=[
                    "Dubai Canal", "Metro station", "Business district",
                    "Restaurants", "Hotels", "Canal walk", "Parks"
                ],
                nearby_landmarks=[
                    "Dubai Canal", "Burj Khalifa", "DIFC", "Downtown Dubai"
                ],
                coordinates=(25.1875, 55.2632),
                developer="Multiple",
                handover_year=2006,
                district="Downtown",
                rental_yield="6-8%",
                investment_score=8,
                family_friendly=False,
                beach_access=False,
                metro_access=True
            ),
            
            "Jumeirah Beach Residence": Community(
                name="Jumeirah Beach Residence",
                tier=CommunityTier.LUXURY,
                price_range_min=1_800_000,
                price_range_max=25_000_000,
                property_types=["apartment", "penthouse"],
                amenities=[
                    "Beach access", "The Walk JBR", "Restaurants",
                    "Beach clubs", "Water sports", "Metro nearby",
                    "Shopping", "Entertainment"
                ],
                nearby_landmarks=[
                    "The Beach", "Ain Dubai", "Dubai Marina", "The Walk"
                ],
                coordinates=(25.0792, 55.1344),
                developer="DMCC",
                handover_year=2007,
                district="Beachfront",
                rental_yield="6-8%",
                investment_score=8,
                family_friendly=True,
                beach_access=True,
                metro_access=True
            ),
            
            "Dubai Creek Harbour": Community(
                name="Dubai Creek Harbour",
                tier=CommunityTier.LUXURY,
                price_range_min=1_500_000,
                price_range_max=20_000_000,
                property_types=["apartment", "villa", "townhouse"],
                amenities=[
                    "Creek views", "Parks", "Marina", "Retail",
                    "Schools", "Healthcare", "Community centers"
                ],
                nearby_landmarks=[
                    "Dubai Creek Tower (under construction)", "Ras Al Khor Wildlife Sanctuary"
                ],
                coordinates=(25.1850, 55.3450),
                developer="Emaar",
                handover_year=2018,
                district="Creek Side",
                rental_yield="6-8%",
                investment_score=9,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "City Walk": Community(
                name="City Walk",
                tier=CommunityTier.LUXURY,
                price_range_min=2_500_000,
                price_range_max=18_000_000,
                property_types=["apartment", "penthouse"],
                amenities=[
                    "Retail boulevard", "Restaurants", "Art galleries",
                    "Parks", "Kids play areas", "Fitness centers"
                ],
                nearby_landmarks=[
                    "City Walk Mall", "Coca-Cola Arena", "Jumeirah"
                ],
                coordinates=(25.2177, 55.2659),
                developer="Meraas",
                handover_year=2015,
                district="Urban Living",
                rental_yield="5-7%",
                investment_score=8,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            # ==========================================
            # PREMIUM COMMUNITIES
            # ==========================================
            "Arabian Ranches": Community(
                name="Arabian Ranches",
                tier=CommunityTier.PREMIUM,
                price_range_min=3_000_000,
                price_range_max=12_000_000,
                property_types=["villa", "townhouse"],
                amenities=[
                    "Golf course", "Polo club", "Schools", "Retail",
                    "Community center", "Parks", "Sports facilities",
                    "Healthcare"
                ],
                nearby_landmarks=[
                    "Arabian Ranches Golf Club", "Ranches Souk", "Dubai Polo & Equestrian Club"
                ],
                coordinates=(25.0526, 55.2760),
                developer="Emaar",
                handover_year=2004,
                district="Family Communities",
                rental_yield="5-7%",
                investment_score=7,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "Dubai Hills Estate": Community(
                name="Dubai Hills Estate",
                tier=CommunityTier.PREMIUM,
                price_range_min=2_500_000,
                price_range_max=15_000_000,
                property_types=["villa", "apartment", "townhouse"],
                amenities=[
                    "Golf course", "Dubai Hills Mall", "Parks",
                    "Schools", "Healthcare", "Community centers",
                    "Sports facilities", "Retail"
                ],
                nearby_landmarks=[
                    "Dubai Hills Mall", "Dubai Hills Golf Club", "Dubai Hills Park"
                ],
                coordinates=(25.1063, 55.2453),
                developer="Emaar",
                handover_year=2017,
                district="Family Communities",
                rental_yield="6-8%",
                investment_score=9,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "Jumeirah Village Circle": Community(
                name="Jumeirah Village Circle",
                tier=CommunityTier.PREMIUM,
                price_range_min=800_000,
                price_range_max=3_000_000,
                property_types=["apartment", "townhouse", "villa"],
                amenities=[
                    "Parks", "Schools", "Retail", "Community centers",
                    "Healthcare", "Sports facilities", "Nurseries"
                ],
                nearby_landmarks=[
                    "Circle Mall", "JVC District Parks", "Ibn Battuta Mall"
                ],
                coordinates=(25.0587, 55.2043),
                developer="Nakheel",
                handover_year=2010,
                district="Family Communities",
                rental_yield="7-9%",
                investment_score=7,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "Dubai Sports City": Community(
                name="Dubai Sports City",
                tier=CommunityTier.PREMIUM,
                price_range_min=900_000,
                price_range_max=3_500_000,
                property_types=["apartment", "townhouse", "villa"],
                amenities=[
                    "Cricket stadium", "Golf course", "Sports academies",
                    "Schools", "Retail", "Community centers"
                ],
                nearby_landmarks=[
                    "ICC Academy", "Els Club Dubai", "Dubai Sports City Cricket Stadium"
                ],
                coordinates=(25.0361, 55.2168),
                developer="Dubai Properties",
                handover_year=2009,
                district="Sports Community",
                rental_yield="7-9%",
                investment_score=6,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "Motor City": Community(
                name="Motor City",
                tier=CommunityTier.PREMIUM,
                price_range_min=1_000_000,
                price_range_max=4_000_000,
                property_types=["apartment", "townhouse", "villa"],
                amenities=[
                    "Dubai Autodrome", "Parks", "Retail", "Schools",
                    "Community centers", "Sports facilities"
                ],
                nearby_landmarks=[
                    "Dubai Autodrome", "Motor City Green Community"
                ],
                coordinates=(25.0447, 55.2467),
                developer="Union Properties",
                handover_year=2008,
                district="Sports Community",
                rental_yield="7-9%",
                investment_score=6,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "Town Square": Community(
                name="Town Square",
                tier=CommunityTier.PREMIUM,
                price_range_min=1_200_000,
                price_range_max=4_500_000,
                property_types=["apartment", "townhouse", "villa"],
                amenities=[
                    "Central park", "Retail", "Schools", "Healthcare",
                    "Community centers", "Sports facilities", "Nurseries"
                ],
                nearby_landmarks=[
                    "Town Square Park", "Nshama Town Square"
                ],
                coordinates=(25.0524, 55.2847),
                developer="Nshama",
                handover_year=2017,
                district="Family Communities",
                rental_yield="7-9%",
                investment_score=8,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            # ==========================================
            # AFFORDABLE COMMUNITIES
            # ==========================================
            "Dubai Silicon Oasis": Community(
                name="Dubai Silicon Oasis",
                tier=CommunityTier.AFFORDABLE,
                price_range_min=400_000,
                price_range_max=1_500_000,
                property_types=["apartment", "studio"],
                amenities=[
                    "Tech park", "Mall", "Sports complex", "Schools",
                    "Healthcare", "Community centers", "Parks"
                ],
                nearby_landmarks=[
                    "DSO Mall", "Academic City", "Dubai Silicon Oasis Authority"
                ],
                coordinates=(25.1189, 55.3793),
                developer="DSOA",
                handover_year=2004,
                district="Tech Hub",
                rental_yield="8-10%",
                investment_score=7,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "Discovery Gardens": Community(
                name="Discovery Gardens",
                tier=CommunityTier.AFFORDABLE,
                price_range_min=350_000,
                price_range_max=900_000,
                property_types=["apartment", "studio"],
                amenities=[
                    "Gardens", "Metro station", "Retail", "Parks",
                    "Community centers", "Schools nearby"
                ],
                nearby_landmarks=[
                    "Ibn Battuta Mall", "Jebel Ali", "The Gardens Mall"
                ],
                coordinates=(25.0438, 55.1292),
                developer="Nakheel",
                handover_year=2008,
                district="Affordable Living",
                rental_yield="8-10%",
                investment_score=6,
                family_friendly=True,
                beach_access=False,
                metro_access=True
            ),
            
            "International City": Community(
                name="International City",
                tier=CommunityTier.AFFORDABLE,
                price_range_min=300_000,
                price_range_max=800_000,
                property_types=["apartment", "studio"],
                amenities=[
                    "Themed clusters", "Retail", "Parks", "Healthcare",
                    "Budget-friendly", "Diverse community"
                ],
                nearby_landmarks=[
                    "Dragon Mart", "International City Center", "Warsan Village"
                ],
                coordinates=(25.1713, 55.4128),
                developer="Nakheel",
                handover_year=2002,
                district="Affordable Living",
                rental_yield="9-11%",
                investment_score=5,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "Dubailand": Community(
                name="Dubailand",
                tier=CommunityTier.AFFORDABLE,
                price_range_min=500_000,
                price_range_max=1_800_000,
                property_types=["apartment", "villa", "townhouse"],
                amenities=[
                    "Upcoming developments", "Sports facilities",
                    "Schools", "Retail", "Large land area"
                ],
                nearby_landmarks=[
                    "IMG Worlds of Adventure", "Dubai Outlet Mall"
                ],
                coordinates=(25.1745, 55.3093),
                developer="Multiple",
                handover_year=2003,
                district="Emerging Area",
                rental_yield="8-10%",
                investment_score=6,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            ),
            
            "Remraam": Community(
                name="Remraam",
                tier=CommunityTier.AFFORDABLE,
                price_range_min=600_000,
                price_range_max=1_500_000,
                property_types=["apartment", "townhouse"],
                amenities=[
                    "Community centers", "Parks", "Retail", "Schools nearby",
                    "Sports facilities", "Swimming pools"
                ],
                nearby_landmarks=[
                    "Arabian Ranches", "Dubai Sports City"
                ],
                coordinates=(25.0342, 55.2556),
                developer="Remraam Community",
                handover_year=2009,
                district="Affordable Living",
                rental_yield="8-10%",
                investment_score=6,
                family_friendly=True,
                beach_access=False,
                metro_access=False
            )
        }
    
    def _initialize_aliases(self) -> Dict[str, str]:
        """Initialize community name aliases"""
        return {
            "marina": "Dubai Marina",
            "downtown": "Downtown Dubai",
            "palm": "Palm Jumeirah",
            "jbr": "Jumeirah Beach Residence",
            "jumeirah beach": "Jumeirah Beach Residence",
            "silicon oasis": "Dubai Silicon Oasis",
            "dso": "Dubai Silicon Oasis",
            "business bay": "Business Bay",
            "jvc": "Jumeirah Village Circle",
            "jumeirah village": "Jumeirah Village Circle",
            "discovery": "Discovery Gardens",
            "arabian ranches": "Arabian Ranches",
            "dubai hills": "Dubai Hills Estate",
            "hills estate": "Dubai Hills Estate",
            "motor city": "Motor City",
            "sports city": "Dubai Sports City",
            "international city": "International City",
            "creek harbour": "Dubai Creek Harbour",
            "city walk": "City Walk",
            "emirates hills": "Emirates Hills",
            "al barari": "Al Barari"
        }
    
    def _initialize_market_insights(self) -> Dict[str, MarketInsight]:
        """Initialize market insights for communities"""
        return {
            "Dubai Marina": MarketInsight(
                community="Dubai Marina",
                avg_price_per_sqft=1800,
                price_trend="stable",
                demand_level="high",
                rental_yield="6-8%",
                investment_potential="high",
                best_for=["Investors", "Young professionals", "Expats", "Beach lovers"]
            ),
            "Downtown Dubai": MarketInsight(
                community="Downtown Dubai",
                avg_price_per_sqft=2200,
                price_trend="stable",
                demand_level="high",
                rental_yield="5-7%",
                investment_potential="high",
                best_for=["Luxury seekers", "Investors", "City living enthusiasts"]
            ),
            "Palm Jumeirah": MarketInsight(
                community="Palm Jumeirah",
                avg_price_per_sqft=2500,
                price_trend="rising",
                demand_level="high",
                rental_yield="4-6%",
                investment_potential="high",
                best_for=["Ultra-luxury buyers", "Beach lovers", "High net worth individuals"]
            ),
            "Dubai Hills Estate": MarketInsight(
                community="Dubai Hills Estate",
                avg_price_per_sqft=1400,
                price_trend="rising",
                demand_level="high",
                rental_yield="6-8%",
                investment_potential="high",
                best_for=["Families", "Investors", "Golf enthusiasts"]
            ),
            "Jumeirah Village Circle": MarketInsight(
                community="Jumeirah Village Circle",
                avg_price_per_sqft=900,
                price_trend="stable",
                demand_level="medium",
                rental_yield="7-9%",
                investment_potential="medium",
                best_for=["First-time buyers", "Families", "Investors"]
            )
        }
    
    # ==========================================
    # QUERY METHODS
    # ==========================================
    
    def find_community(self, query: str) -> Optional[Community]:
        """Find community by name or alias"""
        query_lower = query.lower().strip()
        
        # Direct match
        for name, community in self.communities.items():
            if query_lower == name.lower():
                return community
        
        # Alias match
        if query_lower in self.aliases:
            canonical_name = self.aliases[query_lower]
            return self.communities.get(canonical_name)
        
        # Partial match
        for name, community in self.communities.items():
            if query_lower in name.lower():
                return community
        
        return None
    
    def search_by_budget(
        self,
        min_budget: int,
        max_budget: int,
        tier: Optional[CommunityTier] = None,
        property_type: Optional[str] = None
    ) -> List[Community]:
        """Find communities within budget range"""
        results = []
        
        for community in self.communities.values():
            # Check tier filter
            if tier and community.tier != tier:
                continue
            
            # Check property type filter
            if property_type and property_type not in community.property_types:
                continue
            
            # Check if budget overlaps with community price range
            if (min_budget <= community.price_range_max and 
                max_budget >= community.price_range_min):
                results.append(community)
        
        # Sort by relevance (price match)
        results.sort(key=lambda c: abs(c.price_range_min - min_budget))
        
        return results
    
    def get_communities_by_tier(self, tier: CommunityTier) -> List[Community]:
        """Get all communities in a tier"""
        return [c for c in self.communities.values() if c.tier == tier]
    
    def get_communities_by_amenity(self, amenity: str) -> List[Community]:
        """Find communities with specific amenity"""
        amenity_lower = amenity.lower()
        return [
            c for c in self.communities.values()
            if any(amenity_lower in a.lower() for a in c.amenities)
        ]
    
    def get_beach_communities(self) -> List[Community]:
        """Get all beach/waterfront communities"""
        return [c for c in self.communities.values() if c.beach_access]
    
    def get_metro_accessible_communities(self) -> List[Community]:
        """Get communities with metro access"""
        return [c for c in self.communities.values() if c.metro_access]
    
    def get_family_friendly_communities(self) -> List[Community]:
        """Get family-friendly communities"""
        return [c for c in self.communities.values() if c.family_friendly]
    
    def get_market_insights(self, community_name: str) -> Optional[MarketInsight]:
        """Get market insights for a community"""
        community = self.find_community(community_name)
        if not community:
            return None
        
        # Return cached insights or generate basic ones
        if community.name in self.market_insights:
            return self.market_insights[community.name]
        
        # Generate basic insights
        return MarketInsight(
            community=community.name,
            avg_price_per_sqft=None,
            price_trend="stable",
            demand_level=self._estimate_demand(community),
            rental_yield=community.rental_yield or "6-8%",
            investment_potential=self._calculate_investment_score_text(community),
            best_for=self._determine_best_for(community)
        )
    
    def recommend_communities(
        self,
        budget: Optional[int] = None,
        property_type: Optional[str] = None,
        must_have_amenities: List[str] = [],
        prefer_beach: bool = False,
        prefer_metro: bool = False,
        family_friendly: bool = False,
        limit: int = 5
    ) -> List[Dict]:
        """Smart community recommendations based on requirements"""
        
        scored_communities = []
        
        for community in self.communities.values():
            score = 0
            reasons = []
            
            # Budget match
            if budget:
                if community.price_range_min <= budget <= community.price_range_max:
                    score += 30
                    reasons.append("Within budget")
                elif budget >= community.price_range_min:
                    score += 15
                    reasons.append("Budget sufficient")
            
            # Property type match
            if property_type and property_type in community.property_types:
                score += 20
                reasons.append(f"Has {property_type}s")
            
            # Amenities match
            amenity_matches = sum(
                1 for amenity in must_have_amenities
                if any(amenity.lower() in ca.lower() for ca in community.amenities)
            )
            if amenity_matches > 0:
                score += amenity_matches * 10
                reasons.append(f"{amenity_matches} amenities matched")
            
            # Beach preference
            if prefer_beach and community.beach_access:
                score += 15
                reasons.append("Beach access")
            
            # Metro preference
            if prefer_metro and community.metro_access:
                score += 10
                reasons.append("Metro accessible")
            
            # Family friendly
            if family_friendly and community.family_friendly:
                score += 10
                reasons.append("Family-friendly")
            
            # Investment score boost
            if community.investment_score:
                score += community.investment_score
            
            if score > 0:
                scored_communities.append({
                    "community": community,
                    "score": score,
                    "reasons": reasons
                })
        
        # Sort by score
        scored_communities.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_communities[:limit]
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _estimate_demand(self, community: Community) -> str:
        """Estimate demand level"""
        if community.tier in [CommunityTier.ULTRA_LUXURY, CommunityTier.LUXURY]:
            return "high"
        elif community.tier == CommunityTier.PREMIUM:
            return "medium"
        else:
            return "medium"
    
    def _calculate_investment_score_text(self, community: Community) -> str:
        """Calculate investment potential text"""
        if community.investment_score:
            if community.investment_score >= 8:
                return "high"
            elif community.investment_score >= 6:
                return "medium"
            else:
                return "low"
        return "medium"
    
    def _determine_best_for(self, community: Community) -> List[str]:
        """Determine what type of buyers this community is best for"""
        best_for = []
        
        if community.tier == CommunityTier.ULTRA_LUXURY:
            best_for.extend(["Ultra-luxury buyers", "High net worth individuals"])
        
        if community.beach_access:
            best_for.append("Beach lovers")
        
        if community.family_friendly:
            best_for.append("Families")
        
        if community.metro_access:
            best_for.append("Commuters")
        
        if "golf" in " ".join(community.amenities).lower():
            best_for.append("Golf enthusiasts")
        
        if community.tier == CommunityTier.AFFORDABLE:
            best_for.extend(["First-time buyers", "Investors"])
        
        return best_for if best_for else ["General buyers"]
    
    def get_all_communities(self) -> List[Community]:
        """Get all communities"""
        return list(self.communities.values())
    
    def get_total_communities_count(self) -> int:
        """Get total number of communities"""
        return len(self.communities)


# Global instance
dubai_knowledge = DubaiKnowledge()