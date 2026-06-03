"use client";

import Link from "next/link";
import { useState } from "react";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [nameError, setNameError] = useState(false);
  const [emailError, setEmailError] = useState(false);
  const [passwordError, setPasswordError] =
    useState(false);
  const [confirmPasswordError, setConfirmPasswordError] =
    useState(false);

  const [error, setError] = useState("");

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const resetErrors = () => {
    setNameError(false);
    setEmailError(false);
    setPasswordError(false);
    setConfirmPasswordError(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    setError("");
    resetErrors();

    if (name.trim() === "") {
      setError("Please enter your name.");
      setNameError(true);
      return;
    }

    if (email.trim() === "") {
      setError("Please enter your email.");
      setEmailError(true);
      return;
    }

    if (!validateEmail(email)) {
      setError("Please enter a valid email.");
      setEmailError(true);
      return;
    }

    if (password.trim() === "") {
      setError("Please enter a password.");
      setPasswordError(true);
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      setPasswordError(true);
      return;
    }

    if (confirmPassword.trim() === "") {
      setError("Please confirm your password.");
      setConfirmPasswordError(true);
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      setPasswordError(true);
      setConfirmPasswordError(true);
      return;
    }

    alert("Account created!");
  };

  const inputStyles = (hasError: boolean) =>
    `w-full rounded-xl border px-4 py-3 text-black focus:outline-none focus:ring-2 ${
      hasError
        ? "border-red-500 focus:ring-red-500"
        : "border-gray-300 focus:ring-black"
    }`;

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-3xl font-bold text-center text-black mb-2">
          Create Account
        </h1>

        <p className="text-center text-gray-600 mb-8">
          Sign up to get started
        </p>

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-black mb-1">
              Name
            </label>

            <input
              type="text"
              placeholder="John Doe"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={inputStyles(nameError)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-black mb-1">
              Email
            </label>

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputStyles(emailError)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-black mb-1">
              Password
            </label>

            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputStyles(passwordError)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-black mb-1">
              Confirm Password
            </label>

            <input
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) =>
                setConfirmPassword(e.target.value)
              }
              className={inputStyles(confirmPasswordError)}
            />
          </div>

          {error && (
            <div className="bg-red-100 text-red-700 p-3 rounded-xl text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-black text-white py-3 rounded-xl font-semibold hover:bg-gray-800 transition"
          >
            Sign Up
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-700">
          Already have an account?

          <Link
            href="/login"
            className="ml-2 font-semibold text-black hover:underline"
          >
            Login
          </Link>
        </div>
      </div>
    </div>
  );
}