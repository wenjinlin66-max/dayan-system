export interface AuthIdentity {
  user_id: string
  dept_id: string
  display_name: string
  roles: string[]
}

export interface AuthLoginResponse {
  access_token: string
  token_type: string
  identity: AuthIdentity
}
