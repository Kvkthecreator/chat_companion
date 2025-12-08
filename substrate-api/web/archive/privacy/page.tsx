import type { Metadata } from "next";
import Brand from "@/components/Brand";

export const metadata: Metadata = {
    title: "Privacy Policy",
};

export default function Page() {
    return (
            <div className="prose max-w-3xl mx-auto p-6">
                <h1 className="text-2xl font-bold">Privacy Policy</h1>

                <p>
                    <strong>Effective Date: March 25th, 2025</strong>
                </p>

                <p>
                    This Privacy Policy outlines how <Brand /> yarnnn ("we", "our", or
                    "us") accesses, uses, and protects your information when you
                    authorize the application to connect with your Google
                    account.
                </p>

                <h2>1. Information We Access</h2>
                <ul>
                    <li>Your Google account email address</li>
                    <li>Permission to send emails on your behalf</li>
                    <li>(Optional) Permission to read specific emails</li>
                </ul>
                <p>
                    We do not store email content or credentials. All access is
                    temporary and tied to your explicit Google OAuth consent.
                </p>

                <h2>2. How We Use Your Data</h2>
                <ul>
                    <li>Send emails via your Gmail account</li>
                    <li>
                        Read inbox content if you enable features like summaries
                        or auto replies
                    </li>
                </ul>
                <p>We do not store or share your Gmail content.</p>

                <h2>3. How to Revoke Access</h2>
                <p>
                    Visit{" "}
                    <a href="https://myaccount.google.com/permissions">
                        https://myaccount.google.com/permissions
                    </a>
                    <br />
                    Revoking disables Gmail-related features in <Brand />.
                </p>

                <h2>4. Data Security</h2>
                <p>
                    We use OAuth2 and do not store credentials or Gmail data.
                    All communication with Google APIs is encrypted.
                </p>

                <h2>5. Contact Us</h2>
                <p>
                    📧{" "}
                    <a href="mailto:contactus@yarnnn.com">
                        contactus@yarnnn.com
                    </a>
                </p>
            </div>
    );
}
