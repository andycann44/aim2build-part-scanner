import React from "react";
import V2LegalLayout from "../v2/components/V2LegalLayout";

const PrivacyPage: React.FC = () => {
  return (
    <V2LegalLayout title="Privacy Policy" subtitle="Last updated: 7 February 2026">
        <p>
          Aim2Build ("we", "us", "our") respects your privacy. This policy explains what data we collect, why we
          collect it, and your rights.
        </p>

        <h2>1. Data controller</h2>
        <p>
          <strong>Aim2 Ltd</strong><br />
          <strong>Registered address:</strong> Aim2 Ltd, 49 Dumers Lane, Radcliffe, Manchester M26 2QE, United Kingdom<br />
          <strong>Email:</strong> <a href="mailto:support@aim2build.co.uk">support@aim2build.co.uk</a>
        </p>

        <h2>2. What data we collect</h2>
        <h3>Account data</h3>
        <ul>
          <li>Email address</li>
          <li>User ID</li>
          <li>Encrypted authentication credentials</li>
        </ul>

        <h3>TikTok integration data</h3>
        <p>When you connect TikTok, we may process:</p>
        <ul>
          <li>TikTok account IDs</li>
          <li>OAuth access tokens (and related authentication data needed to connect)</li>
          <li>Media uploads you initiate through the integration</li>
          <li>Posting status and basic analytics (if enabled)</li>
        </ul>
        <p>We do not access private TikTok messages or unrelated account data.</p>

        <h3>User content</h3>
        <ul>
          <li>LEGO inventory data</li>
          <li>Sets, parts, and buildability information you enter</li>
        </ul>

        <h3>Technical data</h3>
        <ul>
          <li>IP address</li>
          <li>Device and browser information</li>
          <li>Log and error data</li>
        </ul>

        <h2>3. Purpose and legal basis</h2>
        <ul>
          <li>Provide and operate the Aim2Build service (contractual necessity)</li>
          <li>Enable TikTok publishing features (consent)</li>
          <li>Improve reliability and performance (legitimate interests)</li>
          <li>Comply with legal obligations (legal obligation)</li>
        </ul>

        <h2>4. Retention</h2>
        <ul>
          <li>Account data is retained while your account is active.</li>
          <li>TikTok tokens are retained only as long as needed to provide the integration, or until you disconnect.</li>
          <li>You can request deletion at any time (see "Your rights").</li>
        </ul>

        <h2>5. Sharing and third parties</h2>
        <p>We do not sell personal data.</p>
        <p>We may share data with:</p>
        <ul>
          <li>TikTok (for authentication and posting you initiate)</li>
          <li>Infrastructure providers (hosting, CDN, email delivery, logging)</li>
          <li>Authorities where required by law</li>
        </ul>

        <h2>6. International transfers</h2>
        <p>
          Some data may be processed outside the UK/EU depending on service providers. Where transfers occur, we use
          appropriate safeguards.
        </p>

        <h2>7. Your rights</h2>
        <p>You have the right to request:</p>
        <ul>
          <li>Access to your data</li>
          <li>Correction of inaccurate data</li>
          <li>Deletion of your data</li>
          <li>Restriction or objection to processing</li>
          <li>Withdrawal of consent (where applicable)</li>
        </ul>
        <p>
          Requests: <a href="mailto:support@aim2build.co.uk">support@aim2build.co.uk</a>
        </p>

        <h2>8. Cookies and analytics</h2>
        <p>
          Aim2Build uses essential cookies to keep the site working. We also use Cloudflare Analytics for basic,
          privacy-focused site traffic measurements. We do not use advertising cookies.
        </p>

        <h2>9. Changes</h2>
        <p>
          We may update this Privacy Policy from time to time. Significant changes will be communicated where
          appropriate.
        </p>

        <h2>10. Contact</h2>
        <p>
          Privacy questions: <a href="mailto:support@aim2build.co.uk">support@aim2build.co.uk</a>
        </p>
    </V2LegalLayout>
  );
};

export default PrivacyPage;
