/**
 * Privacy Policy Page
 */
import { DashboardLayout } from '../components/DashboardLayout'
import '../styles/legal.css'

export function Privacy() {
  return (
    <DashboardLayout title="Privacy Policy" subtitle="Last updated: November 24, 2025">
      <div className="legal-content">
        <section className="legal-section">
          <h2>1. Information We Collect</h2>
          <p>
            ToAllCreation collects information to provide and improve our services. The types of information we collect include:
          </p>

          <h3>1.1 Information You Provide</h3>
          <ul>
            <li><strong>Account Information:</strong> When you create an account, we collect your email address and password.</li>
            <li><strong>Social Media Credentials:</strong> When you connect social media accounts, we store OAuth tokens to post on your behalf.</li>
            <li><strong>Content:</strong> Videos, captions, and other content you upload to share across platforms.</li>
          </ul>

          <h3>1.2 Automatically Collected Information</h3>
          <ul>
            <li><strong>Usage Data:</strong> Information about how you use our service, including upload history and posting activity.</li>
            <li><strong>Device Information:</strong> Browser type, IP address, and device identifiers.</li>
            <li><strong>Cookies:</strong> We use cookies to maintain your session and improve user experience.</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>2. How We Use Your Information</h2>
          <p>We use the information we collect to:</p>
          <ul>
            <li>Provide, maintain, and improve our services</li>
            <li>Post content to your connected social media accounts</li>
            <li>Communicate with you about service updates and support</li>
            <li>Monitor and analyze usage patterns to improve functionality</li>
            <li>Detect, prevent, and address technical issues and security threats</li>
            <li>Comply with legal obligations</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>3. Information Sharing and Disclosure</h2>
          <p>We do not sell your personal information. We may share your information in the following circumstances:</p>

          <h3>3.1 Social Media Platforms</h3>
          <p>
            When you use our service to post content, we share your videos and captions with the social media platforms
            you've connected (Facebook, Instagram, Twitter/X, YouTube, LinkedIn, TikTok) according to your instructions.
          </p>

          <h3>3.2 Service Providers</h3>
          <p>
            We use third-party service providers to help operate our service, including:
          </p>
          <ul>
            <li>Amazon Web Services (AWS) for hosting and infrastructure</li>
            <li>AWS Cognito for authentication services</li>
            <li>AWS S3 for video storage</li>
          </ul>

          <h3>3.3 Legal Requirements</h3>
          <p>
            We may disclose your information if required by law or in response to valid legal requests, such as
            subpoenas, court orders, or government demands.
          </p>
        </section>

        <section className="legal-section">
          <h2>4. Data Storage and Security</h2>
          <p>
            Your data is stored securely using AWS services with industry-standard encryption:
          </p>
          <ul>
            <li><strong>Videos:</strong> Stored in AWS S3 with automatic deletion after 7 days</li>
            <li><strong>Account Data:</strong> Stored in AWS DynamoDB with encryption at rest</li>
            <li><strong>Authentication:</strong> Managed by AWS Cognito with secure token-based authentication</li>
            <li><strong>Transmission:</strong> All data transmitted over HTTPS with TLS encryption</li>
          </ul>
          <p>
            While we implement reasonable security measures, no method of transmission over the Internet or electronic
            storage is 100% secure. We cannot guarantee absolute security.
          </p>
        </section>

        <section className="legal-section">
          <h2>5. Data Retention</h2>
          <ul>
            <li><strong>Videos:</strong> Automatically deleted from S3 after 7 days</li>
            <li><strong>Upload History:</strong> Retained for 90 days, then automatically deleted</li>
            <li><strong>Account Data:</strong> Retained until you delete your account</li>
            <li><strong>Social Media Tokens:</strong> Stored until you disconnect the account</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>6. Your Rights and Choices</h2>
          <p>You have the following rights regarding your information:</p>
          <ul>
            <li><strong>Access:</strong> Request a copy of your personal information</li>
            <li><strong>Correction:</strong> Update or correct your information</li>
            <li><strong>Deletion:</strong> Request deletion of your account and associated data</li>
            <li><strong>Disconnect Accounts:</strong> Remove connected social media accounts at any time</li>
            <li><strong>Opt-out:</strong> Disable cookies through your browser settings (may affect functionality)</li>
          </ul>
          <p>
            To exercise these rights, please contact us at the email address provided below.
          </p>
        </section>

        <section className="legal-section">
          <h2>7. Third-Party Links and Services</h2>
          <p>
            Our service integrates with third-party social media platforms. When you connect these accounts or post content,
            you are subject to those platforms' privacy policies and terms of service. We are not responsible for the
            privacy practices of these third parties.
          </p>
        </section>

        <section className="legal-section">
          <h2>8. Children's Privacy</h2>
          <p>
            Our service is not intended for children under 13 years of age. We do not knowingly collect personal information
            from children under 13. If you believe we have collected information from a child under 13, please contact us
            immediately.
          </p>
        </section>

        <section className="legal-section">
          <h2>9. International Data Transfers</h2>
          <p>
            Your information may be transferred to and processed in countries other than your country of residence.
            These countries may have data protection laws different from your country. By using our service, you consent
            to the transfer of your information to the United States and other countries where we operate.
          </p>
        </section>

        <section className="legal-section">
          <h2>10. Changes to This Privacy Policy</h2>
          <p>
            We may update this Privacy Policy from time to time. We will notify you of significant changes by posting
            the new policy on this page and updating the "Last updated" date. Your continued use of the service after
            changes constitutes acceptance of the updated policy.
          </p>
        </section>

        <section className="legal-section">
          <h2>11. Contact Us</h2>
          <p>
            If you have questions or concerns about this Privacy Policy or our data practices, please contact us at:
          </p>
          <p>
            <strong>Email:</strong> privacy@toallcreation.org<br />
            <strong>Website:</strong> toallcreation.org
          </p>
        </section>

        <section className="legal-section">
          <h2>12. California Privacy Rights</h2>
          <p>
            If you are a California resident, you have additional rights under the California Consumer Privacy Act (CCPA):
          </p>
          <ul>
            <li>Right to know what personal information is collected</li>
            <li>Right to know if personal information is sold or disclosed</li>
            <li>Right to say no to the sale of personal information</li>
            <li>Right to access your personal information</li>
            <li>Right to equal service and price</li>
          </ul>
          <p>
            Note: We do not sell your personal information.
          </p>
        </section>
      </div>
    </DashboardLayout>
  )
}
