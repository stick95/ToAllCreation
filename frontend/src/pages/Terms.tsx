/**
 * Terms and Conditions Page
 */
import { DashboardLayout } from '../components/DashboardLayout'
import '../styles/legal.css'

export function Terms() {
  return (
    <DashboardLayout title="Terms and Conditions" subtitle="Last updated: November 24, 2025">
      <div className="legal-content">
        <section className="legal-section">
          <h2>1. Acceptance of Terms</h2>
          <p>
            By accessing and using ToAllCreation ("Service"), you accept and agree to be bound by these Terms and Conditions
            ("Terms"). If you do not agree to these Terms, please do not use the Service.
          </p>
          <p>
            We reserve the right to modify these Terms at any time. Your continued use of the Service after changes
            constitutes acceptance of the modified Terms.
          </p>
        </section>

        <section className="legal-section">
          <h2>2. Description of Service</h2>
          <p>
            ToAllCreation is a social media management platform that allows users to:
          </p>
          <ul>
            <li>Upload video content for distribution</li>
            <li>Connect multiple social media accounts (Facebook, Instagram, Twitter/X, YouTube, LinkedIn, TikTok)</li>
            <li>Post content simultaneously across connected platforms</li>
            <li>Track posting history and status</li>
          </ul>
          <p>
            The Service is provided "as is" and we reserve the right to modify, suspend, or discontinue any aspect
            of the Service at any time without notice.
          </p>
        </section>

        <section className="legal-section">
          <h2>3. User Accounts</h2>

          <h3>3.1 Account Registration</h3>
          <p>
            To use the Service, you must create an account by providing accurate and complete information. You are
            responsible for maintaining the confidentiality of your account credentials and for all activities under
            your account.
          </p>

          <h3>3.2 Account Security</h3>
          <p>
            You agree to:
          </p>
          <ul>
            <li>Provide accurate, current, and complete information during registration</li>
            <li>Maintain and update your information to keep it accurate</li>
            <li>Maintain the security of your password</li>
            <li>Notify us immediately of any unauthorized account access</li>
            <li>Accept responsibility for all activities under your account</li>
          </ul>

          <h3>3.3 Account Termination</h3>
          <p>
            We reserve the right to suspend or terminate your account if you violate these Terms or engage in
            activities that harm the Service or other users.
          </p>
        </section>

        <section className="legal-section">
          <h2>4. Social Media Account Connections</h2>

          <h3>4.1 Authorization</h3>
          <p>
            By connecting social media accounts, you authorize ToAllCreation to post content on your behalf to those
            platforms. You are responsible for ensuring you have the rights to grant this authorization.
          </p>

          <h3>4.2 Third-Party Terms</h3>
          <p>
            Your use of connected social media platforms is subject to their respective terms of service and policies.
            You are responsible for compliance with all third-party platform requirements.
          </p>

          <h3>4.3 Token Storage</h3>
          <p>
            We securely store OAuth tokens for connected accounts. You may disconnect accounts at any time, which will
            delete the stored tokens.
          </p>
        </section>

        <section className="legal-section">
          <h2>5. Content and Intellectual Property</h2>

          <h3>5.1 Your Content</h3>
          <p>
            You retain all rights to content you upload ("Your Content"). By uploading content, you grant ToAllCreation
            a limited license to:
          </p>
          <ul>
            <li>Store Your Content temporarily for distribution</li>
            <li>Post Your Content to your connected social media accounts</li>
            <li>Process Your Content for delivery to social media platforms</li>
          </ul>
          <p>
            This license terminates when Your Content is deleted from our systems (automatically after 7 days).
          </p>

          <h3>5.2 Content Responsibility</h3>
          <p>
            You are solely responsible for Your Content. You represent and warrant that:
          </p>
          <ul>
            <li>You own or have the necessary rights to Your Content</li>
            <li>Your Content does not violate any laws or third-party rights</li>
            <li>Your Content does not contain malware or harmful code</li>
            <li>Your Content complies with our Content Guidelines</li>
          </ul>

          <h3>5.3 Prohibited Content</h3>
          <p>
            You may not upload content that:
          </p>
          <ul>
            <li>Violates any law or regulation</li>
            <li>Infringes intellectual property rights</li>
            <li>Contains hate speech, harassment, or threats</li>
            <li>Promotes violence or illegal activities</li>
            <li>Contains explicit sexual content or child exploitation material</li>
            <li>Violates privacy rights or contains personal information of others</li>
            <li>Contains malware, viruses, or harmful code</li>
            <li>Impersonates others or misrepresents affiliation</li>
          </ul>

          <h3>5.4 Our Rights</h3>
          <p>
            We reserve the right to remove any content that violates these Terms or is otherwise objectionable,
            without notice.
          </p>
        </section>

        <section className="legal-section">
          <h2>6. Service Usage and Limitations</h2>

          <h3>6.1 Acceptable Use</h3>
          <p>
            You agree not to:
          </p>
          <ul>
            <li>Use the Service for any illegal purpose</li>
            <li>Attempt to gain unauthorized access to the Service</li>
            <li>Interfere with or disrupt the Service or servers</li>
            <li>Use automated systems to access the Service without permission</li>
            <li>Reverse engineer or attempt to extract source code</li>
            <li>Resell or redistribute the Service</li>
          </ul>

          <h3>6.2 Service Limits</h3>
          <ul>
            <li>Maximum video file size: 100MB per upload</li>
            <li>Video storage: 7 days (automatic deletion thereafter)</li>
            <li>Upload history retention: 90 days</li>
          </ul>
          <p>
            We may modify these limits at our discretion.
          </p>
        </section>

        <section className="legal-section">
          <h2>7. Disclaimers and Limitations of Liability</h2>

          <h3>7.1 Service Availability</h3>
          <p>
            We strive to maintain service availability but do not guarantee uninterrupted access. The Service may
            be unavailable due to maintenance, technical issues, or circumstances beyond our control.
          </p>

          <h3>7.2 No Warranty</h3>
          <p>
            THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
            LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
          </p>

          <h3>7.3 Limitation of Liability</h3>
          <p>
            TO THE MAXIMUM EXTENT PERMITTED BY LAW, TOALLCREATION SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL,
            SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR REVENUES, WHETHER INCURRED DIRECTLY
            OR INDIRECTLY, OR ANY LOSS OF DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES, RESULTING FROM:
          </p>
          <ul>
            <li>Your use or inability to use the Service</li>
            <li>Unauthorized access to your account or data</li>
            <li>Service interruptions or errors</li>
            <li>Content posted through the Service</li>
            <li>Third-party platforms or services</li>
          </ul>

          <h3>7.4 Third-Party Services</h3>
          <p>
            We are not responsible for the actions, content, or policies of third-party social media platforms.
            Any issues with posting to third-party platforms are subject to their terms and support.
          </p>
        </section>

        <section className="legal-section">
          <h2>8. Indemnification</h2>
          <p>
            You agree to indemnify and hold harmless ToAllCreation, its officers, directors, employees, and agents
            from any claims, damages, losses, liabilities, and expenses (including legal fees) arising from:
          </p>
          <ul>
            <li>Your use of the Service</li>
            <li>Your violation of these Terms</li>
            <li>Your violation of any rights of another party</li>
            <li>Your Content</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>9. Privacy and Data Protection</h2>
          <p>
            Your use of the Service is subject to our Privacy Policy, which describes how we collect, use, and
            protect your information. By using the Service, you consent to our data practices as described in
            the Privacy Policy.
          </p>
        </section>

        <section className="legal-section">
          <h2>10. Religious Purpose and Content</h2>
          <p>
            ToAllCreation is inspired by the Biblical mandate to "Go into all the world and preach the gospel to
            all creation" (Mark 16:15). While we welcome users of all backgrounds, we reserve the right to prioritize
            content that aligns with Christian values and teachings.
          </p>
        </section>

        <section className="legal-section">
          <h2>11. Dispute Resolution</h2>

          <h3>11.1 Governing Law</h3>
          <p>
            These Terms are governed by the laws of the United States, without regard to conflict of law provisions.
          </p>

          <h3>11.2 Arbitration</h3>
          <p>
            Any disputes arising from these Terms or the Service shall be resolved through binding arbitration,
            except where prohibited by law. You waive any right to participate in class actions.
          </p>

          <h3>11.3 Exceptions</h3>
          <p>
            Either party may seek injunctive relief in court for intellectual property infringement or unauthorized
            access to the Service.
          </p>
        </section>

        <section className="legal-section">
          <h2>12. Modifications to Service and Terms</h2>
          <p>
            We reserve the right to modify or discontinue the Service (or any part thereof) at any time. We also
            reserve the right to modify these Terms at any time. Continued use after modifications constitutes
            acceptance of the modified Terms.
          </p>
        </section>

        <section className="legal-section">
          <h2>13. Termination</h2>
          <p>
            Either party may terminate this agreement at any time. Upon termination:
          </p>
          <ul>
            <li>Your right to use the Service immediately ceases</li>
            <li>Your Content will be deleted according to our retention policy</li>
            <li>Connected social media accounts will be disconnected</li>
            <li>Provisions that should survive termination (indemnification, disclaimers) remain in effect</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>14. Miscellaneous</h2>

          <h3>14.1 Entire Agreement</h3>
          <p>
            These Terms constitute the entire agreement between you and ToAllCreation regarding the Service.
          </p>

          <h3>14.2 Severability</h3>
          <p>
            If any provision of these Terms is found unenforceable, the remaining provisions remain in effect.
          </p>

          <h3>14.3 No Waiver</h3>
          <p>
            Our failure to enforce any right or provision does not constitute a waiver of that right or provision.
          </p>

          <h3>14.4 Assignment</h3>
          <p>
            You may not assign these Terms without our consent. We may assign these Terms without restriction.
          </p>
        </section>

        <section className="legal-section">
          <h2>15. Contact Information</h2>
          <p>
            For questions about these Terms, please contact us at:
          </p>
          <p>
            <strong>Email:</strong> legal@toallcreation.org<br />
            <strong>Website:</strong> toallcreation.org
          </p>
        </section>

        <section className="legal-section">
          <p>
            By using ToAllCreation, you acknowledge that you have read, understood, and agree to be bound by
            these Terms and Conditions.
          </p>
        </section>
      </div>
    </DashboardLayout>
  )
}
