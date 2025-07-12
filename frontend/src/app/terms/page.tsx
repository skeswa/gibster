import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service - Gibster',
  description:
    'Read the Gibster terms of service and understand your rights and responsibilities',
  openGraph: {
    title: 'Terms of Service - Gibster',
    description: 'Our terms of service and usage guidelines',
  },
};

export default function TermsPage() {
  return (
    <div className='min-h-screen bg-gradient-to-br from-violet-100 via-purple-50 to-pink-100 dark:from-gray-900 dark:via-purple-950 dark:to-violet-950'>
      {/* Navigation */}
      <nav className='sticky top-0 z-50 border-b bg-white/70 backdrop-blur-md dark:bg-gray-900/70 dark:border-gray-700/50'>
        <div className='container mx-auto px-4 py-4'>
          <div className='flex items-center justify-between'>
            <Link href='/' className='flex items-center gap-2'>
              <ArrowLeft className='h-5 w-5' />
              <h1 className='text-2xl font-bold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                Gibster
              </h1>
            </Link>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className='container mx-auto px-4 py-12 max-w-4xl'>
        <div className='bg-white dark:bg-gray-900 rounded-lg shadow-xl p-8 md:p-12'>
          <h1 className='text-4xl font-bold mb-8 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
            Terms of Service
          </h1>

          <div className='prose prose-gray dark:prose-invert max-w-none'>
            <p className='text-lg text-gray-600 dark:text-gray-300 mb-6'>
              Last updated: {new Date().toLocaleDateString()}
            </p>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                1. Acceptance of Terms
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                By accessing and using Gibster (&quot;the Service&quot;), you
                agree to be bound by these Terms of Service (&quot;Terms&quot;).
                If you do not agree to these Terms, please do not use the
                Service.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                2. Description of Service
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                Gibster is a calendar synchronization service that automatically
                syncs your Gibney dance studio bookings to your personal
                calendar. The Service requires you to provide your Gibney
                account credentials to access and sync your bookings.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                3. User Accounts
              </h2>
              <h3 className='text-xl font-semibold mb-2 text-gray-800 dark:text-gray-200'>
                Account Creation
              </h3>
              <ul className='list-disc list-inside text-gray-600 dark:text-gray-300 mb-4'>
                <li>You must provide accurate and complete information</li>
                <li>You are responsible for maintaining account security</li>
                <li>You must notify us of any unauthorized access</li>
                <li>One person or entity may not maintain multiple accounts</li>
              </ul>

              <h3 className='text-xl font-semibold mb-2 text-gray-800 dark:text-gray-200'>
                Account Responsibilities
              </h3>
              <p className='text-gray-600 dark:text-gray-300'>
                You are responsible for all activities that occur under your
                account. Keep your password secure and do not share it with
                others.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                4. Acceptable Use
              </h2>
              <p className='text-gray-600 dark:text-gray-300 mb-4'>
                You agree not to:
              </p>
              <ul className='list-disc list-inside text-gray-600 dark:text-gray-300'>
                <li>Use the Service for any illegal or unauthorized purpose</li>
                <li>
                  Attempt to gain unauthorized access to any part of the Service
                </li>
                <li>Interfere with or disrupt the Service or servers</li>
                <li>Transmit any viruses, worms, or malicious code</li>
                <li>
                  Use the Service to violate Gibney&apos;s terms of service
                </li>
                <li>Resell or redistribute the Service without permission</li>
              </ul>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                5. Third-Party Services
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                The Service integrates with Gibney&apos;s website to access your
                bookings. We are not affiliated with Gibney and are not
                responsible for their services, policies, or actions. Your use
                of Gibney&apos;s services is governed by their terms and
                conditions.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                6. Privacy and Data
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                Your use of the Service is also governed by our Privacy Policy.
                By using the Service, you consent to our collection and use of
                your information as described in the Privacy Policy.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                7. Intellectual Property
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                The Service and its original content, features, and
                functionality are owned by Gibster and are protected by
                international copyright, trademark, and other intellectual
                property laws.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                8. Disclaimer of Warranties
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                The Service is provided &quot;as is&quot; and &quot;as
                available&quot; without warranties of any kind, either express
                or implied, including but not limited to:
              </p>
              <ul className='list-disc list-inside text-gray-600 dark:text-gray-300 mt-4'>
                <li>Merchantability or fitness for a particular purpose</li>
                <li>Accuracy, reliability, or completeness of the Service</li>
                <li>Uninterrupted or error-free operation</li>
                <li>Security or safety of your data</li>
              </ul>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                9. Limitation of Liability
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                To the maximum extent permitted by law, Gibster shall not be
                liable for any indirect, incidental, special, consequential, or
                punitive damages, including but not limited to loss of profits,
                data, or use, arising from your use of the Service.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                10. Indemnification
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                You agree to indemnify and hold harmless Gibster and its
                affiliates from any claims, damages, or expenses arising from
                your use of the Service or violation of these Terms.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                11. Termination
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                We may terminate or suspend your account at any time, with or
                without cause or notice. Upon termination, your right to use the
                Service will immediately cease. You may also terminate your
                account at any time by contacting us.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                12. Changes to Terms
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                We reserve the right to modify these Terms at any time. We will
                notify users of any material changes by posting the new Terms on
                this page. Your continued use of the Service after changes
                constitutes acceptance of the new Terms.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                13. Governing Law
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                These Terms shall be governed by and construed in accordance
                with the laws of [Your Jurisdiction], without regard to its
                conflict of law provisions.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                14. Contact Information
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                If you have any questions about these Terms, please contact us
                at:
              </p>
              <p className='text-gray-600 dark:text-gray-300 mt-4'>
                Email: legal@gibster.app
                <br />
                Address: [Your Address]
              </p>
            </section>
          </div>

          <div className='mt-12 flex justify-center'>
            <Link href='/'>
              <Button variant='outline'>
                <ArrowLeft className='h-4 w-4 mr-2' />
                Back to Home
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
