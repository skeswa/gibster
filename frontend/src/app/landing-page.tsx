import Link from 'next/link';
import {
  ArrowRight,
  Calendar,
  CheckCircle,
  Clock,
  RefreshCw,
  Shield,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function LandingPage() {
  return (
    <div className='min-h-screen bg-gradient-to-br from-violet-100 via-purple-50 to-pink-100 dark:from-gray-900 dark:via-purple-950 dark:to-violet-950'>
      {/* Navigation */}
      <nav className='sticky top-0 z-50 border-b bg-white/70 backdrop-blur-md dark:bg-gray-900/70 dark:border-gray-700/50'>
        <div className='container mx-auto px-4 py-4'>
          <div className='flex items-center justify-between'>
            <h1 className='text-2xl font-bold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent'>
              Gibster
            </h1>
            <div className='flex items-center gap-4'>
              <ThemeToggle />
              <Link href='/login'>
                <Button variant='ghost'>Log In</Button>
              </Link>
              <Link href='/register'>
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className='container mx-auto px-4 py-20 text-center'>
        <div className='mx-auto max-w-3xl'>
          <h2 className='mb-6 text-5xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-6xl'>
            Never Miss a Dance Class at Gibney Again
          </h2>
          <p className='mb-8 text-xl text-gray-600 dark:text-gray-300'>
            Automatically sync your Gibney dance bookings to your personal
            calendar. Stay organized and never double-book yourself.
          </p>
          <div className='flex flex-col gap-4 sm:flex-row sm:justify-center'>
            <Link href='/register'>
              <Button
                size='lg'
                className='w-full sm:w-auto bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white'
              >
                Get Started
                <ArrowRight className='ml-2 h-4 w-4' />
              </Button>
            </Link>
            <Link href='#how-it-works'>
              <Button size='lg' variant='outline' className='w-full sm:w-auto'>
                See How It Works
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className='container mx-auto px-4 py-20'>
        <div className='mx-auto max-w-5xl'>
          <h3 className='mb-12 text-center text-3xl font-bold text-gray-900 dark:text-white'>
            Everything You Need to Stay Organized
          </h3>
          <div className='grid gap-8 md:grid-cols-2 lg:grid-cols-3'>
            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <div className='mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600'>
                  <Calendar className='h-6 w-6 text-white' />
                </div>
                <h4 className='mb-2 text-xl font-semibold text-gray-900 dark:text-white'>
                  Calendar Sync
                </h4>
                <p className='text-gray-600 dark:text-gray-300'>
                  Automatically sync all your Gibney bookings to Google
                  Calendar, Apple Calendar, or any calendar app.
                </p>
              </CardContent>
            </Card>

            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <div className='mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-green-500 to-emerald-600'>
                  <RefreshCw className='h-6 w-6 text-white' />
                </div>
                <h4 className='mb-2 text-xl font-semibold text-gray-900 dark:text-white'>
                  Real-Time Updates
                </h4>
                <p className='text-gray-600 dark:text-gray-300'>
                  Your calendar stays up-to-date with automatic syncing. New
                  bookings appear within minutes.
                </p>
              </CardContent>
            </Card>

            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <div className='mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-pink-600'>
                  <Shield className='h-6 w-6 text-white' />
                </div>
                <h4 className='mb-2 text-xl font-semibold text-gray-900 dark:text-white'>
                  Secure & Private
                </h4>
                <p className='text-gray-600 dark:text-gray-300'>
                  Your Gibney credentials are encrypted and stored securely. We
                  never share your data.
                </p>
              </CardContent>
            </Card>

            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <div className='mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-orange-500 to-red-600'>
                  <Clock className='h-6 w-6 text-white' />
                </div>
                <h4 className='mb-2 text-xl font-semibold text-gray-900 dark:text-white'>
                  Save Time
                </h4>
                <p className='text-gray-600 dark:text-gray-300'>
                  No more manual calendar entries. Focus on dancing while we
                  handle the scheduling.
                </p>
              </CardContent>
            </Card>

            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <div className='mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-pink-500 to-rose-600'>
                  <CheckCircle className='h-6 w-6 text-white' />
                </div>
                <h4 className='mb-2 text-xl font-semibold text-gray-900 dark:text-white'>
                  Never Double-Book
                </h4>
                <p className='text-gray-600 dark:text-gray-300'>
                  See all your commitments in one place and avoid scheduling
                  conflicts.
                </p>
              </CardContent>
            </Card>

            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <div className='mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600'>
                  <Calendar className='h-6 w-6 text-white' />
                </div>
                <h4 className='mb-2 text-xl font-semibold text-gray-900 dark:text-white'>
                  Works Everywhere
                </h4>
                <p className='text-gray-600 dark:text-gray-300'>
                  Compatible with all major calendar applications through
                  standard iCal format.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section
        id='how-it-works'
        className='bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm py-20'
      >
        <div className='container mx-auto px-4'>
          <div className='mx-auto max-w-3xl text-center'>
            <h3 className='mb-12 text-3xl font-bold text-gray-900 dark:text-white'>
              How It Works
            </h3>
            <div className='space-y-8'>
              <div className='flex items-start gap-4 text-left'>
                <div className='flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white'>
                  1
                </div>
                <div>
                  <h4 className='mb-2 text-lg font-semibold text-gray-900 dark:text-white'>
                    Sign Up for Gibster
                  </h4>
                  <p className='text-gray-600 dark:text-gray-300'>
                    Create your account in seconds. It&apos;s completely free.
                  </p>
                </div>
              </div>

              <div className='flex items-start gap-4 text-left'>
                <div className='flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white'>
                  2
                </div>
                <div>
                  <h4 className='mb-2 text-lg font-semibold text-gray-900 dark:text-white'>
                    Connect Your Gibney Account
                  </h4>
                  <p className='text-gray-600 dark:text-gray-300'>
                    Securely link your Gibney credentials. They&apos;re
                    encrypted and never shared.
                  </p>
                </div>
              </div>

              <div className='flex items-start gap-4 text-left'>
                <div className='flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white'>
                  3
                </div>
                <div>
                  <h4 className='mb-2 text-lg font-semibold text-gray-900 dark:text-white'>
                    Add to Your Calendar
                  </h4>
                  <p className='text-gray-600 dark:text-gray-300'>
                    Copy your unique calendar URL and add it to any calendar
                    app. That&apos;s it!
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className='container mx-auto px-4 py-20'>
        <div className='mx-auto max-w-4xl'>
          <h3 className='mb-12 text-center text-3xl font-bold text-gray-900 dark:text-white'>
            Loved by Dancers
          </h3>
          <div className='grid gap-8 md:grid-cols-2'>
            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <p className='mb-4 text-gray-600 dark:text-gray-300'>
                  &quot;Gibster has been a game-changer! I used to miss classes
                  because I forgot to check my bookings. Now everything is right
                  in my calendar.&quot;
                </p>
                <p className='font-semibold text-gray-900 dark:text-white'>
                  — Sarah M.
                </p>
              </CardContent>
            </Card>

            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <p className='mb-4 text-gray-600 dark:text-gray-300'>
                  &quot;Simple, reliable, and just works. I love that I can see
                  my dance schedule alongside my work meetings.&quot;
                </p>
                <p className='font-semibold text-gray-900 dark:text-white'>
                  — Michael T.
                </p>
              </CardContent>
            </Card>

            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <p className='mb-4 text-gray-600 dark:text-gray-300'>
                  &quot;The automatic sync is fantastic. I book a class on
                  Gibney and it appears in my calendar within minutes.&quot;
                </p>
                <p className='font-semibold text-gray-900 dark:text-white'>
                  — Jessica R.
                </p>
              </CardContent>
            </Card>

            <Card className='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm'>
              <CardContent className='p-6'>
                <p className='mb-4 text-gray-600 dark:text-gray-300'>
                  &quot;As someone who takes multiple classes per week, Gibster
                  helps me stay organized and never double-book myself.&quot;
                </p>
                <p className='font-semibold text-gray-900 dark:text-white'>
                  — David L.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className='bg-gradient-to-r from-violet-600 to-purple-600 py-20'>
        <div className='container mx-auto px-4 text-center'>
          <div className='mx-auto max-w-2xl'>
            <h3 className='mb-4 text-3xl font-bold text-white'>
              Ready to Simplify Your Dance Schedule?
            </h3>
            <p className='mb-8 text-xl text-purple-100'>
              Join hundreds of dancers who never miss a class.
            </p>
            <Link href='/register'>
              <Button
                size='lg'
                className='bg-white text-purple-600 hover:bg-gray-100'
              >
                Get Started Now
                <ArrowRight className='ml-2 h-4 w-4' />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className='border-t bg-white/70 dark:bg-gray-900/70 backdrop-blur-sm dark:border-gray-700/50'>
        <div className='container mx-auto px-4 py-8'>
          <div className='flex flex-col items-center justify-between gap-4 sm:flex-row'>
            <p className='text-gray-600 dark:text-gray-300'>
              © 2024 Gibster. All rights reserved.
            </p>
            <div className='flex gap-6'>
              <Link
                href='/privacy'
                className='text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              >
                Privacy Policy
              </Link>
              <Link
                href='/terms'
                className='text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white'
              >
                Terms of Service
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
