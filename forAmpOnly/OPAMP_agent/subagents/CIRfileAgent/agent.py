
from google.adk.agents import LlmAgent
GEMINI_MODEL = "gemini-2.0-flash"

CIR_file_agent = LlmAgent(
    name="CIRfileAgent",
    # https://ai.google.dev/gemini-api/docs/models
    model="gemini-2.0-flash",
    description="Make Analog OPAMP Design CIR",
    instruction="""
    You are a helpful .cir file Agent for ngspice . 
    
    Based on the previous OPAMP information:{opamp_info}, 
    the example .cir file with simulation (cir_example), the input .cir 
    file without simulation (cir_target) and DC infomation {DC_simulate}

    Response with a .cir like text with simulation from cir_target 
    following the example .cir file. 
    This output .cir file will be fed to ngspice.
    Remember to check the definition, like using the .model part from the .cir example for nmos. For other passive component, it is not needed.
    Otherwise the NGspice reports an error.
    Here is an example:
        .model mmod numos
        + x.mesh l=0.0 n=1
        + x.mesh l=0.6 n=4
        + x.mesh l=0.7 n=5
        + x.mesh l=1.0 n=7
        + x.mesh l=1.2 n=11
        + x.mesh l=3.2 n=21
        + x.mesh l=3.4 n=25
        + x.mesh l=3.7 n=27
        + x.mesh l=3.8 n=28
        + x.mesh l=4.4 n=31
        +
        + y.mesh l=-.05 n=1
        + y.mesh l=0.0  n=5
        + y.mesh l=.05  n=9
        + y.mesh l=0.3  n=14
        + y.mesh l=2.0  n=19
        +
        + region num=1 material=1 y.l=0.0
        + material num=1 silicon
        + mobility material=1 concmod=sg fieldmod=sg
        + mobility material=1 elec major
        + mobility material=1 elec minor
        + mobility material=1 hole major
        + mobility material=1 hole minor
        +
        + region num=2 material=2 y.h=0.0 x.l=0.7 x.h=3.7
        + material num=2 oxide
        +
        + elec num=1 x.l=3.8 x.h=4.4	y.l=0.0 y.h=0.0
        + elec num=2 x.l=0.7 x.h=3.7	iy.l=1  iy.h=1
        + elec num=3 x.l=0.0 x.h=0.6	y.l=0.0 y.h=0.0
        + elec num=4 x.l=0.0 x.h=4.4	y.l=2.0 y.h=2.0
        +
        + doping unif p.type conc=2.5e16 x.l=0.0 x.h=4.4  y.l=0.0 y.h=2.0
        + doping unif p.type conc=1e16   x.l=0.0 x.h=4.4  y.l=0.0 y.h=0.05
        + doping unif n.type conc=1e20   x.l=0.0 x.h=1.1  y.l=0.0 y.h=0.2
        + doping unif n.type conc=1e20   x.l=3.3 x.h=4.4  y.l=0.0 y.h=0.2
        +
        + models concmob fieldmob
        + method ac=direct onec
    """,
    output_key ="CIR_file"
    #maybe in 1, use current source in the future
    # before_agent_callback=modify_attachment
)