
class FoodStandard(object):

    def __init__(self):

        self.size = {  #  key          label     
                        "chunky":"Chunky",
                        "fine":"Fine particles",
                        "mix":"Mix",
                    }

        self.moisture = {  #  key   label         lb ub   
                            "dry":["Dry/powdered",0,10],
                            "swet":["Slightly wet",10,30],
                            "wet":["Wet",30,50],
                            "liquid":["Liquid",50,70],
                            "not sure":["Not sure",70,100]
                        }

        self.homogeneity = {  #  key              label   lb ub   
                        "Pure":          ["Pure",100,100],
                        "Slightly Mixed":["Slightly Mixed (<10%)",90,100],
                        "Medially mixed":["Medially mixed (10-30%)",70,90],
                        "Largely Mixed": ["Largely Mixed (>30%)",0,70]
                    }


class ManureStandard(object):

    def __init__(self):

        self.moisture = {  #  key          label         lb ub   
                            "Very Low":["Very Low (<10%)",0,10],
                            "Low":["Low (10-30%)",10,30],
                            "Mid":["Mid (30-50%)",30,50],
                            "High":["High (50-70%)",50,70],
                            "Very High":["Very High (>70%)",70,100]
                        }

        self.homogeneity = {  #  key              label   lb ub   
                                "Pure":          ["Pure",100,100],
                                "Slightly Mixed":["Slightly Mixed (<10%)",90,100],
                                "Medially mixed":["Medially mixed (10-30%)",70,90],
                                "Largely Mixed": ["Largely Mixed (>30%)",0,70]
                           }

class WoodStandard(object):

    def __init__(self):

        self.moisture = {  #  key   label      lb ub   
                            "Low":["Low (<10%)",0,10],
                            "Mid":["Mid (10-30%)",10,30],
                            "High":["High (>30%)",30,100]
                        }

        self.homogeneity = {  #  key              label   lb ub   
                                "Pure":          ["Pure",100,100],
                                "Slightly Mixed":["Slightly Mixed (<10%)",90,100],
                                "Medially mixed":["Medially mixed (10-30%)",70,90],
                                "Largely Mixed": ["Largely Mixed (>30%)",0,70]
                           }

        self.type = {  #  key              label
                        "Horticulture Waste": "Horticulture Waste",
                        "Wooden Pallets": "Wooden Pallets",
                        "Packaging (crates/boxes)": "Packaging (crates/boxes)",
                        "Furniture/Joinery": "Furniture/Joinery",
                        "Construction (wooden planks/materials)": "Construction (wooden planks/materials)",
                        "Demolition/Remodeling": "Demolition/Remodeling",
                        "Others": "Others"

                    }

        self.size = {  #  key              label  
                        "Bulky Item": "Bulky Item (>100cm)",
                        "Large Piece":"Large Piece (50-100cm)",
                        "Medium Piece":"Medium Piece (10-50cm)",
                        "Small Piece": "Small Piece (<10cm)"
                    }

