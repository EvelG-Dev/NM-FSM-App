# terraform.tfvars actual values
# Overrides defaults in variables.tf
# Committed to Git (no secrets here)

db_name = "fsm_db"
db_user = "flaskapp"

# db_password is intentionally NOT stored here.
# It comes from TF_VAR_db_password.
