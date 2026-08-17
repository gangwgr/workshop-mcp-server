/**
 * Slash command handler for MCP web GUI chat inputs.
 * Usage: type /help, /mode cursor, /status, /preset health_check, etc.
 */
(function(global) {
    'use strict';

    var context = {
        scope: 'global',
        onAnalyze: null,
        onPreset: null,
        onScript: null,
        onTriage: null,
        onClear: null,
    };

    function setContext(opts) {
        context = Object.assign({}, context, opts || {});
    }

    function isSlashCommand(text) {
        return (text || '').trim().indexOf('/') === 0;
    }

    function appendChatMessage(containerSelector, sender, html) {
        var $c = $(containerSelector);
        if (!$c.length) return;
        var bubble = sender === 'user'
            ? '<div style="background:#805ad5;color:white;padding:0.75rem;border-radius:0.5rem;max-width:85%;margin-left:auto;">' + html + '</div>'
            : '<div style="background:white;padding:0.75rem;border-radius:0.5rem;flex:1;box-shadow:0 1px 2px rgba(0,0,0,0.05);">' + html + '</div>';
        var row = sender === 'user'
            ? '<div class="chat-message user-message" style="margin-bottom:0.75rem;display:flex;justify-content:flex-end;">' + bubble + '</div>'
            : '<div class="chat-message assistant-message" style="margin-bottom:0.75rem;display:flex;align-items:start;gap:0.75rem;"><div style="background:#4299e1;color:white;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fas fa-terminal" style="font-size:0.75rem;"></i></div>' + bubble + '</div>';
        $c.append(row);
        $c[0].scrollTop = $c[0].scrollHeight;
    }

    function formatMarkdown(text) {
        if (typeof window.formatMarkdown === 'function') return window.formatMarkdown(text);
        return $('<div>').text(text).html().replace(/\n/g, '<br>');
    }

    function runServerCommand(text, scope) {
        return $.ajax({
            url: '/api/commands/run',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ input: text, scope: scope || context.scope || 'global' })
        });
    }

    function handleSlashCommand(text, chatMessagesSelector) {
        var deferred = $.Deferred();

        if (text === '/analyze' && typeof context.onAnalyze === 'function') {
            context.onAnalyze();
            deferred.resolve({ handled: true, message: 'Started analysis on this page.' });
            return deferred.promise();
        }

        if (text.indexOf('/preset ') === 0 && typeof context.onPreset === 'function') {
            var preset = text.replace('/preset ', '').trim();
            context.onPreset(preset);
            deferred.resolve({ handled: true, message: 'Preset set to **' + preset + '**. Click Analyze to run.' });
            return deferred.promise();
        }

        if (text.indexOf('/script ') === 0 && typeof context.onScript === 'function') {
            var scriptId = text.replace('/script ', '').trim();
            var scriptResult = context.onScript(scriptId);
            if (scriptResult && scriptResult.handled === false) {
                deferred.resolve(scriptResult);
            } else {
                deferred.resolve({ handled: true, message: 'Running script **' + scriptId + '**…' });
            }
            return deferred.promise();
        }

        if (text.indexOf('/triage ') === 0 && typeof context.onTriage === 'function') {
            var workflowId = text.replace('/triage ', '').trim();
            var triageResult = context.onTriage(workflowId);
            if (triageResult && triageResult.handled === false) {
                deferred.resolve(triageResult);
            } else {
                deferred.resolve({ handled: true, message: 'Running triage workflow **' + workflowId + '**…' });
            }
            return deferred.promise();
        }

        if (text === '/clear' && typeof context.onClear === 'function') {
            context.onClear();
            deferred.resolve({ handled: true, message: 'Chat cleared.', silent: true });
            return deferred.promise();
        }

        if (text.indexOf('/debug ') === 0) {
            var issue = encodeURIComponent(text.replace('/debug ', '').trim());
            window.location.href = '/cluster-debugger?issue=' + issue;
            deferred.resolve({ handled: true, message: 'Opening Cluster Debugger…' });
            return deferred.promise();
        }

        if (text.indexOf('/mustgather ') === 0) {
            var path = encodeURIComponent(text.replace('/mustgather ', '').trim());
            window.location.href = '/mustgather-analyzer?bundle=' + path;
            deferred.resolve({ handled: true, message: 'Opening Must-Gather Analyzer…' });
            return deferred.promise();
        }

        runServerCommand(text, context.scope).done(function(resp) {
            deferred.resolve(resp);
        }).fail(function(xhr) {
            deferred.resolve({
                handled: true,
                message: (xhr.responseJSON && xhr.responseJSON.error) || 'Command failed'
            });
        });

        return deferred.promise();
    }

    function interceptChatSubmit(formSelector, inputSelector, chatMessagesSelector) {
        $(formSelector).off('submit.slash').on('submit.slash', function(e) {
            var text = $(inputSelector).val().trim();
            if (!isSlashCommand(text)) return;

            e.preventDefault();
            e.stopImmediatePropagation();

            appendChatMessage(chatMessagesSelector, 'user', $('<div>').text(text).html());

            handleSlashCommand(text, chatMessagesSelector).done(function(resp) {
                $(inputSelector).val('');
                if (resp.silent) return;
                var msg = resp.message || resp.output || 'Done.';
                if (resp.format === 'markdown' || resp.command === 'help') {
                    msg = formatMarkdown(msg);
                } else {
                    msg = $('<div>').text(msg).html().replace(/\n/g, '<br>');
                }
                appendChatMessage(chatMessagesSelector, 'assistant', msg);
                if (resp.action === 'switch_mode' && resp.mode) {
                    $('#modeSelect').val(resp.mode);
                    if (typeof updateIndicator === 'function') updateIndicator(resp);
                    if (typeof updateModelDropdown === 'function') updateModelDropdown(resp);
                    if (typeof populateLlmModeSelect === 'function') populateLlmModeSelect(resp);
                }
            });
        });
    }

    global.MCPSlashCommands = {
        setContext: setContext,
        isSlashCommand: isSlashCommand,
        handleSlashCommand: handleSlashCommand,
        interceptChatSubmit: interceptChatSubmit,
        appendChatMessage: appendChatMessage
    };
})(window);
