/**
 * AWS Cognito Authentication Client
 * Lightweight Cognito implementation without AWS Amplify
 */

interface CognitoConfig {
  region: string
  userPoolId: string
  clientId: string
}

interface AuthTokens {
  accessToken: string
  idToken: string
  refreshToken: string
  expiresIn: number
}

interface CognitoUser {
  username: string
  email?: string
  sub: string
  emailVerified?: boolean
}

export class CognitoAuth {
  private config: CognitoConfig
  private cognitoUrl: string

  constructor(config: CognitoConfig) {
    this.config = config
    this.cognitoUrl = `https://cognito-idp.${config.region}.amazonaws.com`
  }

  /**
   * Sign up a new user
   */
  async signUp(email: string, password: string): Promise<{ userSub: string }> {
    const response = await fetch(this.cognitoUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.SignUp'
      },
      body: JSON.stringify({
        ClientId: this.config.clientId,
        Username: email,
        Password: password,
        UserAttributes: [
          { Name: 'email', Value: email }
        ]
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Sign up failed')
    }

    const data = await response.json()
    return { userSub: data.UserSub }
  }

  /**
   * Confirm email with verification code
   */
  async confirmSignUp(email: string, code: string): Promise<void> {
    const response = await fetch(this.cognitoUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.ConfirmSignUp'
      },
      body: JSON.stringify({
        ClientId: this.config.clientId,
        Username: email,
        ConfirmationCode: code
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Confirmation failed')
    }
  }

  /**
   * Sign in with email and password
   */
  async signIn(email: string, password: string): Promise<AuthTokens> {
    const response = await fetch(this.cognitoUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
      },
      body: JSON.stringify({
        ClientId: this.config.clientId,
        AuthFlow: 'USER_PASSWORD_AUTH',
        AuthParameters: {
          USERNAME: email,
          PASSWORD: password
        }
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Sign in failed')
    }

    const data = await response.json()

    if (!data.AuthenticationResult) {
      throw new Error('Authentication failed - no tokens returned')
    }

    return {
      accessToken: data.AuthenticationResult.AccessToken,
      idToken: data.AuthenticationResult.IdToken,
      refreshToken: data.AuthenticationResult.RefreshToken,
      expiresIn: data.AuthenticationResult.ExpiresIn
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await fetch(this.cognitoUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
      },
      body: JSON.stringify({
        ClientId: this.config.clientId,
        AuthFlow: 'REFRESH_TOKEN_AUTH',
        AuthParameters: {
          REFRESH_TOKEN: refreshToken
        }
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Token refresh failed')
    }

    const data = await response.json()

    return {
      accessToken: data.AuthenticationResult.AccessToken,
      idToken: data.AuthenticationResult.IdToken,
      refreshToken: refreshToken, // Refresh token doesn't change
      expiresIn: data.AuthenticationResult.ExpiresIn
    }
  }

  /**
   * Sign out (client-side only)
   */
  signOut(): void {
    // Client-side sign out - just clear local tokens
    // For global sign out, need to call GlobalSignOut API
  }

  /**
   * Forgot password - initiate password reset
   */
  async forgotPassword(email: string): Promise<void> {
    const response = await fetch(this.cognitoUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.ForgotPassword'
      },
      body: JSON.stringify({
        ClientId: this.config.clientId,
        Username: email
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Password reset request failed')
    }
  }

  /**
   * Confirm password reset with code
   */
  async confirmPassword(email: string, code: string, newPassword: string): Promise<void> {
    const response = await fetch(this.cognitoUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.ConfirmForgotPassword'
      },
      body: JSON.stringify({
        ClientId: this.config.clientId,
        Username: email,
        ConfirmationCode: code,
        Password: newPassword
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Password reset failed')
    }
  }

  /**
   * Decode JWT token to get user info (without verification)
   * Note: This is client-side only - server must verify token!
   */
  decodeToken(token: string): CognitoUser | null {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )

      const payload = JSON.parse(jsonPayload)

      return {
        username: payload['cognito:username'] || payload.username,
        email: payload.email,
        sub: payload.sub,
        emailVerified: payload.email_verified
      }
    } catch (error) {
      console.error('Failed to decode token:', error)
      return null
    }
  }

  /**
   * Check if token is expired
   */
  isTokenExpired(token: string): boolean {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )

      const payload = JSON.parse(jsonPayload)
      const exp = payload.exp * 1000 // Convert to milliseconds
      return Date.now() >= exp
    } catch (error) {
      return true // Assume expired if can't decode
    }
  }
}

// Singleton instance
let cognitoAuth: CognitoAuth | null = null

export function getCognitoAuth(): CognitoAuth {
  if (!cognitoAuth) {
    const config: CognitoConfig = {
      region: import.meta.env.VITE_COGNITO_REGION || 'us-west-2',
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || '',
      clientId: import.meta.env.VITE_COGNITO_CLIENT_ID || ''
    }

    if (!config.userPoolId || !config.clientId) {
      throw new Error('Cognito configuration missing. Set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_CLIENT_ID')
    }

    cognitoAuth = new CognitoAuth(config)
  }

  return cognitoAuth
}
