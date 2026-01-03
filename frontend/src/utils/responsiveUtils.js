/**
 * Responsive Utilities - Dynamic calculations based on screen size
 */

/**
 * Calculate items per page based on screen width
 * @param {number} width - Window inner width
 * @returns {number} - Number of items to display per page
 */
export function getItemsPerPage(width) {
  if (width < 480) {
    return 3; // Very small phones
  } else if (width < 768) {
    return 4; // Phones
  } else if (width < 1024) {
    return 6; // Tablets
  } else if (width < 1440) {
    return 10; // Small laptops
  } else if (width < 1920) {
    return 12; // Standard desktops
  } else {
    return 15; // Large screens
  }
}

/**
 * Hook for responsive items per page that updates on window resize
 * @returns {number} - Current items per page based on screen size
 */
export function useResponsiveItemsPerPage() {
  const [itemsPerPage, setItemsPerPage] = React.useState(
    getItemsPerPage(window.innerWidth)
  );

  React.useEffect(() => {
    const handleResize = () => {
      setItemsPerPage(getItemsPerPage(window.innerWidth));
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return itemsPerPage;
}
