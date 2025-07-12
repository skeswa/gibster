import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy - Gibster',
  description:
    'Learn how Gibster protects your privacy and handles your data securely',
  openGraph: {
    title: 'Privacy Policy - Gibster',
    description: 'Our commitment to protecting your privacy and data',
  },
};

export default function PrivacyPage() {
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
            Privacy Policy
          </h1>

          <div className='prose prose-gray dark:prose-invert max-w-none'>
            <p className='text-lg text-gray-600 dark:text-gray-300 mb-6'>
              Last updated: {new Date().toLocaleDateString()}
            </p>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                Introduction
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                Gibster (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) is
                committed to protecting your privacy. This Privacy Policy
                explains how we collect, use, and safeguard your information
                when you use our service.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                Information We Collect
              </h2>
              <h3 className='text-xl font-semibold mb-2 text-gray-800 dark:text-gray-200'>
                Account Information
              </h3>
              <ul className='list-disc list-inside text-gray-600 dark:text-gray-300 mb-4'>
                <li>Email address</li>
                <li>Password (encrypted)</li>
                <li>Gibney account credentials (encrypted)</li>
              </ul>

              <h3 className='text-xl font-semibold mb-2 text-gray-800 dark:text-gray-200'>
                Booking Data
              </h3>
              <ul className='list-disc list-inside text-gray-600 dark:text-gray-300'>
                <li>Dance class bookings from Gibney</li>
                <li>Class times, locations, and instructors</li>
                <li>Booking status and history</li>
              </ul>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                How We Use Your Information
              </h2>
              <p className='text-gray-600 dark:text-gray-300 mb-4'>
                We use your information to:
              </p>
              <ul className='list-disc list-inside text-gray-600 dark:text-gray-300'>
                <li>Sync your Gibney bookings to your calendar</li>
                <li>Authenticate and maintain your account</li>
                <li>Send notifications about sync status</li>
                <li>Improve our service</li>
              </ul>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                Data Security
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                We implement industry-standard security measures to protect your
                data:
              </p>
              <ul className='list-disc list-inside text-gray-600 dark:text-gray-300 mt-4'>
                <li>All passwords are hashed using bcrypt</li>
                <li>
                  Gibney credentials are encrypted using Fernet encryption
                </li>
                <li>HTTPS encryption for all data transmission</li>
                <li>Regular security audits and updates</li>
              </ul>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                Data Sharing
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                We do not sell, trade, or share your personal information with
                third parties except:
              </p>
              <ul className='list-disc list-inside text-gray-600 dark:text-gray-300 mt-4'>
                <li>With Gibney&apos;s website for booking synchronization</li>
                <li>When required by law or legal process</li>
                <li>To protect our rights or safety</li>
              </ul>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                Your Rights
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                You have the right to:
              </p>
              <ul className='list-disc list-inside text-gray-600 dark:text-gray-300 mt-4'>
                <li>Access your personal data</li>
                <li>Update or correct your information</li>
                <li>Delete your account and associated data</li>
                <li>Opt-out of non-essential communications</li>
              </ul>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                Data Retention
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                We retain your data only as long as necessary to provide our
                services. Booking history is kept for up to 1 year. You may
                request deletion of your data at any time.
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                Contact Us
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                If you have questions about this Privacy Policy or your data,
                please contact us at:
              </p>
              <p className='text-gray-600 dark:text-gray-300 mt-4'>
                Email: privacy@gibster.app
                <br />
                Address: [Your Address]
              </p>
            </section>

            <section className='mb-8'>
              <h2 className='text-2xl font-semibold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
                Changes to This Policy
              </h2>
              <p className='text-gray-600 dark:text-gray-300'>
                We may update this Privacy Policy from time to time. We will
                notify you of any changes by posting the new Privacy Policy on
                this page and updating the &quot;Last updated&quot; date.
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
