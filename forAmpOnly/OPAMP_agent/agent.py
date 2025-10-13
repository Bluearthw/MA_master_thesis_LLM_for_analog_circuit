from google.adk.agents import Agent


# def modify_attachment(callback_context: CallbackContext) -> Optional[types.Content]:
#     """
#     Logs entry and checks 'AMP_agent' in session state.
#     If True, returns Content to skip the agent's execution.
#     If False or not present, returns None to allow execution.
#     """
#     agent_name = callback_context.agent_name
#     invocation_id = callback_context.invocation_id
#     current_state = callback_context.state.to_dict()

#     parts_reformatted = []
#     for part in callback_context.user_content.parts:
#         if hasattr(part, 'inline_data') and part.inline_data and hasattr(part.inline_data, 'data'):
#             mime_type = part.inline_data.mime_type
#             if mime_type == "message/rfc822":
#                 email_content_bytes = part.inline_data.data
#                 # print(email_content_bytes)
#                 processed_email = process_email_content(email_content_bytes)
#                 email_body = _extract_text_from_html(processed_email['body_html'])
#                 email_headers = processed_email['headers']
#                 str_email_headers = json.dumps(email_headers, indent=4)
#                 str_email_content = f"""Headers:
#                 {str_email_headers}

#                 Body:
#                 {email_body}
#                 """
#                 parts_reformatted.append(types.Part(text=str_email_content))
#                 attached_pdfs = [attachment for attachment in processed_email['attachments'] if attachment['content_type'].startswith('application/pdf')]
#                 pdf_mime_type = "application/pdf"    
#                 # attach first email as text
                
#                 for pdf in attached_pdfs:
#                     pdf_artifact = types.Part(inline_data=types.Blob(data=pdf['data'], mime_type=pdf_mime_type))
#                     parts_reformatted.append(pdf_artifact)
#         else:
#             parts_reformatted.append(part)
                
#     callback_context.user_content.parts = parts_reformatted

root_agent = Agent(
    name="OPAMP_agent",
    # https://ai.google.dev/gemini-api/docs/models
    model="gemini-2.0-flash",
    description="Analog OPAMP Design Information agent",
    instruction="""
    You are a helpful Analog OPAMP Design Information Agent. 
    
    You should understand SPICE netlist (.cir) and circuit explanation (.md) from the user.

    1 Format your response as a well-structured report section with:
    2 Number of ports of the netlist, specify the input ports [in] and output ports with [out]
    3 Number of transistors used
    4 The type of the circuit
    5 The specifications that are important
    6 The simulation that the circuit should go through

    """,
    # before_agent_callback=modify_attachment
)
