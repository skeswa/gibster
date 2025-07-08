import React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import AuthenticatedLayout from '@/components/AuthenticatedLayout';

export default function ThemeDemoPage() {
  return (
    <AuthenticatedLayout>
      <div className='space-y-8'>
      <div>
        <h1 className='text-4xl font-bold mb-2'>Theme Demo</h1>
        <p className='text-muted-foreground'>
          This page demonstrates the dark mode theme functionality. Use the
          theme toggle in the header to switch between light, dark, and system
          themes.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Card Component</CardTitle>
          <CardDescription>
            This is a card component that adapts to the current theme.
          </CardDescription>
        </CardHeader>
        <CardContent className='space-y-4'>
          <div className='flex gap-2'>
            <Button>Primary Button</Button>
            <Button variant='secondary'>Secondary</Button>
            <Button variant='outline'>Outline</Button>
            <Button variant='ghost'>Ghost</Button>
            <Button variant='destructive'>Destructive</Button>
          </div>

          <div className='flex gap-2'>
            <Badge>Default</Badge>
            <Badge variant='secondary'>Secondary</Badge>
            <Badge variant='outline'>Outline</Badge>
            <Badge variant='destructive'>Destructive</Badge>
          </div>
        </CardContent>
      </Card>

      <Alert>
        <AlertTitle>Alert Component</AlertTitle>
        <AlertDescription>
          This alert component also adapts to the current theme settings.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Form Elements</CardTitle>
        </CardHeader>
        <CardContent className='space-y-4'>
          <div className='space-y-2'>
            <Label htmlFor='email'>Email</Label>
            <Input id='email' type='email' placeholder='Enter your email' />
          </div>
          <div className='space-y-2'>
            <Label htmlFor='password'>Password</Label>
            <Input
              id='password'
              type='password'
              placeholder='Enter your password'
            />
          </div>
        </CardContent>
      </Card>

      <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
        <Card>
          <CardHeader>
            <CardTitle>Feature 1</CardTitle>
          </CardHeader>
          <CardContent>
            <p className='text-muted-foreground'>
              This is a feature card that demonstrates how multiple cards look
              in the current theme.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Feature 2</CardTitle>
          </CardHeader>
          <CardContent>
            <p className='text-muted-foreground'>
              All components automatically adapt to the selected theme
              preference.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Feature 3</CardTitle>
          </CardHeader>
          <CardContent>
            <p className='text-muted-foreground'>
              The theme preference is persisted across page reloads and
              sessions.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
    </AuthenticatedLayout>
  );
}
