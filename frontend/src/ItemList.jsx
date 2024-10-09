import { useEffect, useState } from 'react';
import axios from 'axios'; // Import axios

const ItemList = () => {
    const [items, setItems] = useState([]); // State to hold fetched data
    const [loading, setLoading] = useState(true); // State for loading indicator
    const [error, setError] = useState(null); // State for error handling

    useEffect(() => {
        // Fetch data from API when component mounts using Axios
        axios
            .get('http://localhost:8081/itemController/api/item') // Replace with your API endpoint
            .then((response) => {
                setItems(response.data); // Set the data into state
                setLoading(false); // Turn off loading state
            })
            .catch((error) => {
                setError(error);
                setLoading(false); // Stop loading if there is an error
            });
    }, []); // Empty array ensures this runs once when the component mounts

    if (loading) return <div>Loading...</div>; // Display while data is loading

    if (error) return <div>Error: {error.message}</div>; // Display any errors

    return (
        <div>
            <h2>Item List</h2>
            <ul>
                {items.map((item) => (
                    <li key={item.item_id}>
                        <strong>{item.item_name}</strong>: {item.energy_Kcal} Kcal
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default ItemList;
