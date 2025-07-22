'use client';

import React, { useState } from 'react';
import Image from "next/image";

const UserProfile = () => {
  const [isActive, setIsActive] = useState(true);
  
  return (
    <div className="bg-gray-100 text-blue-600 border-blue-600 text-sm">
      <Image src="/avatar.jpg" alt="user" className="border-red-500"  width={200} height={200} />
      <h1 className="text-base">Profile</h1>
      <p className="leading-normal text-sm">Description</p>
      <button onClick={() => setIsActive(!isActive)}>Toggle</button>
    </div>
  );
};

export default UserProfile;