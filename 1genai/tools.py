clean_netlist_declaration = { 
    "name": "clean_netlist",
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