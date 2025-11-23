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