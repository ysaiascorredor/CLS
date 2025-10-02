import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';

export function TermsOfService() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="link" className="p-0 h-auto">Terms of Service</Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Terms of Service</DialogTitle>
          <DialogDescription>
            Construction Labor Solution LLC - CSA Safety Audit Platform
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 text-sm">
          <section>
            <h3 className="font-semibold mb-2">1. Acceptance of Terms</h3>
            <p>
              By accessing and using the CSA Construction Safety Audit platform ("Service"), 
              you accept and agree to be bound by the terms and provision of this agreement.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-2">2. Service Description</h3>
            <p>
              CSA provides digital construction safety audit tools, reporting capabilities, 
              and compliance tracking for construction professionals. The platform enables 
              users to conduct safety inspections, generate reports, and maintain compliance records.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-2">3. User Responsibilities</h3>
            <ul className="list-disc ml-4 space-y-1">
              <li>Users must provide accurate and complete information</li>
              <li>Users are responsible for maintaining account security</li>
              <li>Users must comply with all applicable safety regulations and local laws</li>
              <li>Users acknowledge that this platform assists but does not replace professional safety expertise</li>
            </ul>
          </section>

          <section>
            <h3 className="font-semibold mb-2">4. Safety and Compliance Disclaimer</h3>
            <p className="bg-yellow-50 p-3 rounded border-l-4 border-yellow-400">
              <strong>IMPORTANT:</strong> This platform provides tools to assist with safety audits 
              but does not guarantee compliance with all applicable safety regulations. Users remain 
              solely responsible for ensuring full compliance with OSHA, local safety codes, and 
              industry standards. Construction Labor Solution LLC is not liable for any safety 
              incidents, violations, or non-compliance issues.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-2">5. Subscription and Payments</h3>
            <ul className="list-disc ml-4 space-y-1">
              <li>Subscription fees are billed monthly or annually as selected</li>
              <li>All payments are processed securely through Stripe</li>
              <li>Refunds are subject to our refund policy</li>
              <li>Service may be suspended for non-payment</li>
            </ul>
          </section>

          <section>
            <h3 className="font-semibold mb-2">6. Data and Privacy</h3>
            <p>
              We collect and process data in accordance with our Privacy Policy. 
              Audit data belongs to the user but may be processed for service delivery and improvement.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-2">7. Limitation of Liability</h3>
            <p>
              Construction Labor Solution LLC shall not be liable for any indirect, 
              incidental, special, consequential or punitive damages, including without 
              limitation, loss of profits, data, use, goodwill, or other intangible losses.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-2">8. Governing Law</h3>
            <p>
              These terms shall be governed by and construed in accordance with the laws 
              of the United States and the state where Construction Labor Solution LLC is incorporated.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-2">9. Contact Information</h3>
            <p>
              For questions about these terms, please contact us at: 
              <br />
              Email: ysaias.corredor@clsolution.net
              <br />
              Company: Construction Labor Solution LLC
            </p>
          </section>

          <section>
            <p className="text-xs text-gray-500 mt-6">
              Last updated: {new Date().toLocaleDateString()}
            </p>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function PrivacyPolicy() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="link" className="p-0 h-auto">Privacy Policy</Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Privacy Policy</DialogTitle>
          <DialogDescription>
            How Construction Labor Solution LLC protects your data
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 text-sm">
          <section>
            <h3 className="font-semibold mb-2">1. Information We Collect</h3>
            <ul className="list-disc ml-4 space-y-1">
              <li>Account information (name, email, company details)</li>
              <li>Audit data (site information, findings, photos, reports)</li>
              <li>Usage data (how you interact with our platform)</li>
              <li>Payment information (processed securely by Stripe)</li>
            </ul>
          </section>

          <section>
            <h3 className="font-semibold mb-2">2. How We Use Your Information</h3>
            <ul className="list-disc ml-4 space-y-1">
              <li>Provide and improve our safety audit services</li>
              <li>Generate reports and analytics</li>
              <li>Process payments and manage subscriptions</li>
              <li>Send service updates and notifications</li>
              <li>Ensure platform security and prevent fraud</li>
            </ul>
          </section>

          <section>
            <h3 className="font-semibold mb-2">3. Data Sharing</h3>
            <p>
              We do not sell or share your personal information with third parties except:
            </p>
            <ul className="list-disc ml-4 space-y-1">
              <li>With your explicit consent</li>
              <li>To comply with legal obligations</li>
              <li>With service providers who assist in platform operation (Stripe for payments)</li>
              <li>To protect our rights and prevent fraud</li>
            </ul>
          </section>

          <section>
            <h3 className="font-semibold mb-2">4. Data Security</h3>
            <p>
              We implement industry-standard security measures including:
            </p>
            <ul className="list-disc ml-4 space-y-1">
              <li>Encrypted data transmission (HTTPS/SSL)</li>
              <li>Secure user authentication (JWT tokens)</li>
              <li>Regular security updates and monitoring</li>
              <li>Limited access controls for our team</li>
            </ul>
          </section>

          <section>
            <h3 className="font-semibold mb-2">5. Your Rights</h3>
            <p>You have the right to:</p>
            <ul className="list-disc ml-4 space-y-1">
              <li>Access your personal data</li>
              <li>Correct inaccurate information</li>
              <li>Delete your account and data</li>
              <li>Export your audit data</li>
              <li>Opt-out of marketing communications</li>
            </ul>
          </section>

          <section>
            <h3 className="font-semibold mb-2">6. Data Retention</h3>
            <p>
              We retain your data for as long as your account is active or as needed to 
              provide services. Audit records may be retained for compliance purposes 
              even after account deletion, as required by construction industry regulations.
            </p>
          </section>

          <section>
            <h3 className="font-semibold mb-2">7. Contact Us</h3>
            <p>
              For privacy-related questions or to exercise your rights:
              <br />
              Email: ysaias.corredor@clsolution.net
              <br />
              Company: Construction Labor Solution LLC
            </p>
          </section>

          <section>
            <p className="text-xs text-gray-500 mt-6">
              Last updated: {new Date().toLocaleDateString()}
            </p>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}