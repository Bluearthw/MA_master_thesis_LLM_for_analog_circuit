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