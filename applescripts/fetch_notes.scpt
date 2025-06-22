on formatDate(d)
        set monthNames to {"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"}
        set mon to month of d
        set m to 1
        repeat with i from 1 to 12
            if mon = (item i of monthNames) then
                set m to i
                exit repeat
            end if
        end repeat

        set y to year of d
        set dDay to day of d
        set h to hours of d
        set min to minutes of d
        set s to seconds of d

        return y & "-" & my pad(m) & "-" & my pad(dDay) & "-" & my pad(h) & "-" & my pad(min) & "-" & my pad(s)
    end formatDate

    on pad(n)
        if n < 10 then
            return "0" & (n as text)
        else
            return n as text
        end if
    end pad

    set output to ""
    tell application "Notes"
        repeat with theNote in notes
            set noteTitle to the name of theNote
            set noteBody to the body of theNote
            try
                set rawDate to the creation date of theNote
                set noteCreated to my formatDate(rawDate)
            on error
                set noteCreated to ""
            end try
            try
                set rawDate to the modification date of theNote
                set noteModified to my formatDate(rawDate)
            on error
                set noteModified to ""
            end try
            try
                set folderName to the name of the container of theNote
            on error
                set folderName to ""
            end try

            set output to output & noteTitle & "|||SEP|||" & noteBody & "|||SEP|||" & noteCreated & "|||SEP|||" & noteModified & "|||SEP|||" & folderName & "|||END|||"
        end repeat
    end tell
    return output