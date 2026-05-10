from pydantic import BaseModel, Field
class Struct_specs_sim(BaseModel):
    spec: str = Field(description="The name of the specification e.g., 'gain', 'bandwidth'. Different specs may require same simulation. e.g., gain and bandwidth both require ac simulation.")
    # sim_name: str = Field(description="corresponding simulation name. Different specs may require same simulation. e.g., gain and bandwidth both require ac simulation.")
    sim_file_name : str =Field(description="corresponding name of simulations output files. Here are .csv files in the wrdata lines from the generated SPICE netlist. Example: ac_gain.csv")
    spec_id: int = Field(description="Specification ID. There is a table about it. Example: 0=DC Gain. ")

class Struct_flow(BaseModel):
    netlist: str = Field(description="The SPICE netlist. Use standard newlines (\\n) between every line.")
    spec_sims : list[Struct_specs_sim] = Field(description="specifications required and simulations needed")
    is_diff: bool = Field(description="If the circuit is differential output, this field is True.")
    is_CMFB: bool = Field(description="If the circuit has CMFB, this field is True.")

class Struct_flow_type6(BaseModel):
    netlist: str = Field(description="The SPICE netlist. Use standard newlines (\\n) between every line.")
    spec_sims : list[Struct_specs_sim] = Field(description="specifications required and simulations needed")
    is_diff: bool = Field(description="If the circuit is differential output, this field is True.")
    is_CMFB: bool = Field(description="If the circuit has CMFB, this field is True.")
    target_dc_vout: float = Field(description="Define a target DC output voltage based on the circuit.")
        
class Struct_debug(BaseModel):
    netlist: str = Field(description="The SPICE netlist. Use standard newlines (\\n) between every line.")
    spec_sims : list[Struct_specs_sim] = Field(description="simulations needed and why")
    
    # sim_file_names : list[str] =Field(description="list of names of simulations output files. Here are .csv files, e.g., ac_gain.csv and noise.csv")
    fix_info: str = Field(description="what is fixed in the netlist based on the error message and why")

class Struct_cmfb_agent(BaseModel):
    netlist: str = Field(description="The SPICE netlist. Use standard newlines (\\n) between every line.")
    spec_sims : Struct_specs_sim = Field(description="CMFB stability. id is 20")
    
clean_netlist_declaration = { 
    "name": "clean_netlist",# it is a mistery, how does it find the utils.clean_netlist
    "description": "Standardizes and cleans an analog SPICE netlist string by removing parentheses, renaming 'nmos4/pmos4' models, and removing descriptive words like 'resistor/capacitor'.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "netlist": {
                "type": "string",
                "description": "The raw SPICE netlist content as a single string to be cleaned.",
            }
        },
        "required": ["netlist"],
    },
}

add_params_declaration = { 
    "name": "add_params",
    "description": " Add parameters to the transistors, resistors and capacitors in the incomplete spice netlist.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "netlist": {
                "type": "string",
                "description": "The raw SPICE netlist content as a single string to be filled parameters.",
            }
        },
        "required": ["netlist"],
    },
}

add_DC_source_declaration = { 
    "name": "add_DC_source",
    "description": " Add DC source and GND to the incomplete spice netlist.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "netlist": {
                "type": "string",
                "description": "The raw SPICE netlist content as a single string to be added source.",
            }
        },
        "required": ["netlist"],
    },
}

add_C_load_declaration = { 
    "name": "add_C_load",
    "description": " Add load capacitance to the incomplete spice netlist.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "netlist": {
                "type": "string",
                "description": "The raw SPICE netlist content as a single string to be added source.",
            },
            "node": {
                "type": "string",
                "description": "The node name that the load capacitor should be connected to besides VSS.",
            }
        },
        "required": ["netlist", "node"],
    },
}

add_OP_simulation_declaration = { 
    "name": "add_OP_simulation",
    "description": " Add DC input source abd OP operation to the incomplete spice netlist.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "netlist": {
                "type": "string",
                "description": "The raw SPICE netlist content as a single string to be added source.",
            },
            "node": {
                "type": "string",
                "description": "The node name that the DC input source should be connected to besides VSS.",
            }
        },
        "required": ["netlist", "node"],
    },
}
