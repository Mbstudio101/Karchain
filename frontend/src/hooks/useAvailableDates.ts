import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAvailableDates } from "../api";
import { getLocalISODate } from "../lib/utils";

export const useAvailableDates = () => {
    const [availableDates, setAvailableDates] = useState<string[]>([]);
    const [defaultDate, setDefaultDate] = useState<string>("");

    const { data: dates } = useQuery({
        queryKey: ["availableDates"],
        queryFn: fetchAvailableDates,
        staleTime: 1000 * 60 * 5,
    });

    useEffect(() => {
        if (dates && dates.length > 0) {
            setAvailableDates(dates);

            // Find the next available date from today
            const today = getLocalISODate();
            const nextAvailableDate = dates.find(date => date >= today) || dates[0];
            setDefaultDate(nextAvailableDate);
        }
    }, [dates]);

    return { availableDates, defaultDate };
};
