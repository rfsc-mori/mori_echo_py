if status is-interactive
    function fish_user_key_bindings
        # ctrl+l
        bind \cl 'clear; printf "\e[3J"; commandline -f repaint'

        # ctrl+del
        bind \e\[3\;5~ kill-word

        # ctrl+backspace
        bind \cH backward-kill-path-component
    end
end
