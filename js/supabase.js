/**
 * supabase.js - Supabase client initialization and auth
 *
 * Handles Google Sign-In and exposes the Supabase client
 * for use by storage.js.
 */

const SupabaseAuth = (function () {
  const SUPABASE_URL = 'https://clihopnowqjmgstyfqci.supabase.co';
  const SUPABASE_ANON_KEY = 'sb_publishable_lTDbbUhHtqbGMvgFR1KHow_2z_2HXob';

  // Initialize the Supabase client
  const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

  let currentUser = null;

  /**
   * Sign in with Google OAuth.
   */
  function signInWithGoogle() {
    return supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin + window.location.pathname,
      },
    });
  }

  /**
   * Sign out the current user.
   */
  function signOut() {
    return supabase.auth.signOut();
  }

  /**
   * Get the current logged-in user (or null).
   */
  function getUser() {
    return currentUser;
  }

  /**
   * Check if user is logged in.
   */
  function isLoggedIn() {
    return currentUser !== null;
  }

  /**
   * Initialize auth state listener.
   * @param {function} onAuthChange - callback(user) called when auth state changes
   */
  function init(onAuthChange) {
    // Listen for auth state changes
    supabase.auth.onAuthStateChange(function (event, session) {
      currentUser = session ? session.user : null;
      if (onAuthChange) onAuthChange(currentUser);
    });

    // Check existing session
    return supabase.auth.getSession().then(function (result) {
      var session = result.data.session;
      currentUser = session ? session.user : null;
      if (onAuthChange) onAuthChange(currentUser);
      return currentUser;
    });
  }

  /**
   * Get the raw Supabase client (for storage.js queries).
   */
  function getClient() {
    return supabase;
  }

  // ---------- food database search ----------

  function searchFoods(query, limit) {
    if (!supabase) return Promise.resolve([]);
    limit = limit || 30;
    return supabase
      .from('foods')
      .select('name, calories, protein, carbs, fat')
      .ilike('name', '%' + query + '%')
      .limit(limit)
      .then(function (res) {
        return (res.data || []);
      });
  }

  return {
    init: init,
    signInWithGoogle: signInWithGoogle,
    signOut: signOut,
    getUser: getUser,
    isLoggedIn: isLoggedIn,
    getClient: getClient,
    searchFoods: searchFoods,
  };
})();
