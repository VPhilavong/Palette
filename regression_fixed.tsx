"use client";

import React, { useCallback, useState } from 'react';
import Image from "next/image";

interface ProfileStat {
  label: string;
  value: number | string;
}
interface UserProfileData {
  name: string;
  username: string;
  bio: string;
  avatarUrl: string;
  stats: ProfileStat[];
  links?: { label: string; url: string }[];
}

type UserProfilePageProps = {
  /**
   * User profile data to display.
   */
  user?: UserProfileData;
  /**
   * If loading, show skeleton loader.
   */
  loading?: boolean;
  /**
   * If error, display error state.
   */
  error?: string;
};

const DEFAULT_USER: UserProfileData = {
  name: "Taylor West",
  username: "taylorwest",
  bio: "Building the future of planet-based SaaS. Coffee enthusiast, designer, and aspiring astronaut 🌌",
  avatarUrl: "https://ui-avatars.com/api/?background=random&name=Taylor+West",
  stats: [
    { label: "Followers", value: 1280 },
    { label: "Following", value: 215 },
    { label: "Posts", value: 48 },
  ],
  links: [
    { label: "Website", url: "https://taylorwest.com" },
    { label: "GitHub", url: "https://github.com/taylorwest" },
  ],
};

export default function UserProfilePage({ user, loading, error }: UserProfilePageProps) {
  const [isFollowing, setIsFollowing] = useState(false);

  const handleFollowClick = useCallback(() => {
    setIsFollowing((v) => !v);
  }, []);

  if (error) {
    return (
      <section
        className="flex flex-col items-center justify-center min-h-[60vh] bg-gray-100 rounded-lg shadow-md p-8"
        aria-live="polite"
      >
        <span className="text-lg font-semibold text-gray-900 mb-4">Something went wrong</span>
        <span className="text-base text-gray-600">Unable to load user profile.</span>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="flex flex-col items-center min-h-[60vh] justify-center bg-gray-100 rounded-lg shadow-md p-8 animate-pulse">
        <div className="w-24 h-24 rounded-full bg-gray-100 mb-4"></div>
        <div className="h-6 w-40 bg-gray-100 rounded mb-2"></div>
        <div className="h-4 w-24 bg-gray-100 rounded mb-4"></div>
        <div className="h-4 w-64 bg-gray-100 rounded mb-2"></div>
        <div className="h-4 w-48 bg-gray-100 rounded mb-6"></div>
        <div className="flex gap-4">
          <div className="h-10 w-24 bg-gray-100 rounded"></div>
          <div className="h-10 w-24 bg-gray-100 rounded"></div>
        </div>
      </section>
    );
  }

  const profile = user ?? DEFAULT_USER;

  return (
    <section className="flex flex-col items-center w-full max-w-2xl mx-auto mt-8 mb-12 px-4 md:px-8">
      <div className="relative w-full bg-white/80 backdrop-blur rounded-xl shadow-xl p-8 flex flex-col items-center gap-6 transition-shadow hover:shadow-lg">
        <div className="relative group">
          <Image
            src={profile.avatarUrl}
            alt={`${profile.name} profile photo`}
            width={112}
            height={112}
            className="rounded-full border-4 border-blue-600 shadow-md transition-transform group-hover:scale-105 duration-200"
            priority
          />
          <span className="absolute bottom-2 right-2 w-5 h-5 bg-emerald-500 border-2 border-white rounded-full" aria-label="Online status"></span>
        </div>
        <div className="flex flex-col items-center text-center space-y-2">
          <h1 className="text-lg font-bold text-gray-900">{profile.name}</h1>
          <span className="text-base text-gray-600">@{profile.username}</span>
          <p className="text-base text-gray-600 max-w-xl">{profile.bio}</p>
        </div>
        <div className="flex flex-row gap-8 mt-4">
          {profile.stats.map((stat) => (
            <div key={stat.label} className="flex flex-col items-center">
              <span className="text-lg font-bold text-gray-900">{stat.value}</span>
              <span className="text-xs text-gray-600">{stat.label}</span>
            </div>
          ))}
        </div>
        <div className="flex flex-row gap-4 mt-6">
          <button
            type="button"
            className={`px-6 py-2 rounded-md shadow-sm font-semibold text-base transition-all duration-150  ${
              isFollowing
                ? "bg-gray-100 text-gray-900 hover:bg-black hover:text-white"
                : "bg-black text-white hover:bg-blue-600"
            } focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2`}
            aria-pressed={isFollowing}
            aria-label={isFollowing ? "Unfollow user" : "Follow user"}
            onClick={handleFollowClick}
          >
            {isFollowing ? "Following" : "Follow"}
          </button>
          <a
            href={`mailto:contact@${profile.username}.com`}
            className="px-6 py-2 rounded-md shadow-sm bg-blue-600 text-white font-semibold text-base transition-all duration-150 hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2"
            aria-label="Send message"
          >
            Message
          </a>
        </div>
        {profile.links && profile.links.length > 0 && (
          <div className="flex flex-wrap items-center justify-center gap-4 mt-6">
            {profile.links.map((link) => (
              <a
                key={link.url}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 underline hover:text-indigo-600 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-600 rounded-sm px-2 py-1"
                aria-label={`Visit ${link.label}`}
              >
                {link.label}
              </a>
            ))}
          </div>
        )}
      </div>
      <div className="w-full mt-12 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white/70 backdrop-blur rounded-lg shadow-md p-6 transition-shadow hover:shadow-lg">
          <h2 className="text-base font-semibold text-gray-900 mb-4">About</h2>
          <p className="text-base text-gray-600">
            Passionate about building delightful user experiences and bringing ideas to life. Always learning, always exploring.
          </p>
        </div>
        <div className="bg-white/70 backdrop-blur rounded-lg shadow-md p-6 transition-shadow hover:shadow-lg">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Skills</h2>
          <ul className="flex flex-wrap gap-2">
            <li className="bg-blue-600 text-white text-xs px-4 py-2 rounded-sm">React</li>
            <li className="bg-emerald-500 text-white text-xs px-4 py-2 rounded-sm">Tailwind CSS</li>
            <li className="bg-gray-100 text-gray-900 text-xs px-4 py-2 rounded-sm">Next.js</li>
            <li className="bg-indigo-600 text-white text-xs px-4 py-2 rounded-sm">UI/UX</li>
          </ul>
        </div>
      </div>
    </section>
  );
}