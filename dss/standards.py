
class FoodStandard(object):

    def __init__(self):

        self.size = {  #  key          label     
                        "Chunky":"Chunky",
                        "Fine particles":"Fine particles",
                        "Mix":"Mix",
                    }

        self.moisture = {  #  key   label         lb ub   
                            "Dry/powdered":["Dry/powdered",0.0,10.0],
                            "Slightly wet":["Slightly wet",10.0,30.0],
                            "Wet":["Wet",30.0,50.0],
                            "Liquid":["Liquid",50.0,100.0]
                        }

        self.homogeneity = {  #  key              label   lb ub   
                        "Pure":          ["Pure",100.0,100.0],
                        "Slightly Mixed":["Slightly Mixed (<10%)",90.0,100.0],
                        "Medially Mixed":["Medially Mixed (10-30%)",70.0,90.0],
                        "Largely Mixed": ["Largely Mixed (>30%)",0.0,70.0]
                    }


class ManureStandard(object):

    def __init__(self):

        self.moisture = {  #  key          label         lb ub   
                            "Very Low":["Very Low (<10%)",0.0,10.0],
                            "Low":["Low (10-30%)",10.0,30.0],
                            "Moderate":["Moderate (30-50%)",30.0,50.0],
                            "High":["High (50-70%)",50.0,70.0],
                            "Very High":["Very High (>70%)",70.0,100.0]
                        }

        self.homogeneity = {  #  key              label   lb ub   
                                "Pure":          ["Pure",100.0,100.0],
                                "Slightly Mixed":["Slightly Mixed (<10%)",90.0,100.0],
                                "Medially Mixed":["Medially Mixed (10-30%)",70.0,90.0],
                                "Largely Mixed": ["Largely Mixed (>30%)",0.0,70.0]
                           }

class WoodStandard(object):

    def __init__(self):

        self.moisture = {  #  key   label      lb ub   
                            "Low":["Low (<10%)",0.0,10.0],
                            "Moderate":["Moderate (10-30%)",10.0,30.0],
                            "High":["High (>30%)",30.0,100.0]
                        }

        self.homogeneity = {  #  key              label   lb ub   
                                "Pure":          ["Pure",100.0,100.0],
                                "Slightly Mixed":["Slightly Mixed (<10%)",90.0,100.0],
                                "Medially Mixed":["Medially Mixed (10-30%)",70.0,90.0],
                                "Largely Mixed": ["Largely Mixed (>30%)",0.0,70.0]
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

