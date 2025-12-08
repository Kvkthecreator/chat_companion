import type { Metadata } from "next";
import Brand from "@/components/Brand";

export const metadata: Metadata = {
    title: "Terms of Service",
};

export default function Page() {
    return (
            <div className="prose max-w-3xl mx-auto p-6">
                <h1 className="text-2xl font-bold">Terms of Service</h1>

                <p>
                    <strong>Effective Date: March 28th, 2025</strong>
                </p>

                <p>
                    Welcome to <Brand className="" /> yarnnn. By using our app or site,
                    you agree to these Terms of Service. If you disagree, do not
                    use the services.
                </p>

                <h2>1. Use of Services</h2>
                <p>You must:</p>
                <ul>
                    <li>Be 18+ years old</li>
                    <li>Use the service lawfully</li>
                    <li>
                        Authorize secure OAuth access to Gmail when required
                    </li>
                </ul>

                <h2>2. User Data & Gmail Access</h2>
                <p>We may request access to:</p>
                <ul>
                    <li>Your email address</li>
                    <li>Send emails on your behalf</li>
                    <li>(Optionally) Read inbox content</li>
                </ul>
                <p>
                    We don't store Gmail content. Access can be revoked at{" "}
                    <a href="https://myaccount.google.com/permissions">
                        https://myaccount.google.com/permissions
                    </a>
                    .
                </p>

                <h2>3. Restrictions</h2>
                <p>You may not:</p>
                <ul>
                    <li>Send spam</li>
                    <li>Disrupt or reverse-engineer the platform</li>
                    <li>Violate laws or third-party rights</li>
                </ul>
                <p>Violations may result in suspension.</p>

                <h2>4. Modifications</h2>
                <p>
                    We may update these terms and notify you if changes are
                    material. Continued use means acceptance.
                </p>

                <h2>5. Termination</h2>
                <p>
                    We may suspend or terminate access for violating these
                    terms.
                </p>

                <h2>6. Disclaimers</h2>
                <p>
                    <Brand /> is provided "as is" with no warranties. We do our
                    best to ensure reliability but offer no uptime guarantees.
                </p>

                <h2>7. Contact</h2>
                <p>
                    📧{" "}
                    <a href="mailto:contactus@yarnnn.com">
                        contactus@yarnnn.com
                    </a>
                </p>
            </div>
    );
}
