            print(f"⚠️ Alerte : Le client {c_id} n'a pas de web_id associé dans la DB Desktop.")

        deadlines = controller.get_client_deadlines_combined(c_id, w_id)
        