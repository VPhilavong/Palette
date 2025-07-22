import React from "react";
import Image from "next/image";

/**
 * ProfileCardProps interface
 * @prop name - User's full name
 * @prop title - User's title or role
 * @prop description - Short profile description/about
 * @prop avatarUrl - Profile image URL
 * @prop actions - Optional React nodes for footer actions (buttons/links)
 * @prop className - Optional extra className
 * @prop loading - Show loading state if true
 * @prop error - Show error state if string provided
 */
export interface ProfileCardProps {
  name: string;
  title: string;
  description?: string;
  avatarUrl?: string;
  actions?: React.ReactNode;
  className?: string;
  loading?: boolean;
  error?: string;
}

const AVATAR_PLACEHOLDER =
  "https://ui-avatars.com/api/?background=gray&color=fff&name=U";

/**
 * ProfileCard component
 */
const ProfileCard: React.FC<ProfileCardProps> = ({
  name,
  title,
  description,
  avatarUrl,
  actions,
  className = "",
  loading = false,
  error,
}) => {
  // Error and loading states
  if (loading) {
    return (
      <article
        aria-busy="true"
        aria-label="Loading profile card"
        className={`w-full max-w-sm mx-auto bg-white bg-opacity-80 backdrop-blur shadow-md rounded-lg p-6 animate-pulse flex flex-col items-center gap-4 ${className}`}
      >
        <div className="w-24 h-24 rounded-full bg-gray-100 animate-pulse" />
        <div className="h-4 w-32 bg-gray-100 rounded-md" />
        <div className="h-3 w-24 bg-gray-100 rounded-md" />
        <div className="h-3 w-48 bg-gray-100 rounded-md mt-2" />
        <div className="flex gap-2 mt-4">
          <div className="h-8 w-20 bg-blue-600 rounded-sm" />
          <div className="h-8 w-20 bg-emerald-600 rounded-sm" />
        </div>
      </article>
    );
  }

  if (error) {
    return (
      <article
        aria-label="Profile card error"
        className={`w-full max-w-sm mx-auto bg-white bg-opacity-90 backdrop-blur shadow-md rounded-lg p-6 flex flex-col items-center gap-4 border border-red-500 ${className}`}
      >
        <div className="text-red-500 text-base font-semibold" role="alert">
          {error}
        </div>
      </article>
    );
  }

  return (
    <article
      className={`group w-full max-w-sm mx-auto bg-white bg-opacity-80 backdrop-blur shadow-md hover:shadow-lg transition-all duration-300 rounded-lg p-6 flex flex-col items-center gap-6 ${className}`}
      tabIndex={0}
      aria-label={`Profile card for ${name}`}
    >
      <header className="flex flex-col items-center w-full">
        <div className="relative">
          <Image
            src={avatarUrl || AVATAR_PLACEHOLDER}
            alt={`${name}'s avatar`}
            className="w-24 h-24 object-cover aspect-square rounded-full border-4 border-blue-600 shadow-sm bg-gray-100"
            loading="lazy"
           width={200} height={200} />
          <span
            className="absolute bottom-1 right-1 w-4 h-4 bg-emerald-600 rounded-full border-2 border-white"
            aria-label="Online"
            title="Online"
          />
        </div>
        <h2 className="text-lg font-bold text-blue-600 mt-4 text-center">
          {name}
        </h2>
        <p className="text-base font-semibold text-gray-600 mt-1 text-center">
          {title}
        </p>
      </header>
      {description && (
        <section className="w-full text-center mt-2">
          <p className="text-sm text-gray-600 text-sm">{description}</p>
        </section>
      )}
      <footer className="flex gap-4 w-full justify-center mt-4">
        {actions ? (
          actions
        ) : (
          <>
            <button
              type="button"
              className="px-4 py-2 rounded-sm shadow-sm bg-blue-600 text-white text-sm font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue focus:ring-offset-2"
              aria-label="Send message"
            >
              Message
            </button>
            <button
              type="button"
              className="px-4 py-2 rounded-sm shadow-sm bg-emerald-600 text-white text-sm font-semibold transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-emerald focus:ring-offset-2"
              aria-label="Connect"
            >
              Connect
            </button>
          </>
        )}
      </footer>
    </article>
  );
};

export default ProfileCard;