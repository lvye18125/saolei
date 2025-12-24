% De-embed inductor measurements from CSV files.
% Expected columns (first 9 columns used):
% Freq(Hz), S11(dB), S11(deg), S21(dB), S21(deg), S12(dB), S12(deg), S22(dB), S22(deg)

clear; clc;

% ---- File inputs ----
files = struct(...
    'dut1', 'inductor_dut_1.csv', ...
    'short1', 'inductor_short_1.csv', ...
    'open1', 'inductor_open_1.csv', ...
    'dut2', 'inductor_dut_2.csv', ...
    'short2', 'inductor_short_2.csv', ...
    'open2', 'inductor_open_2.csv' ...
);

% ---- Reference impedance ----
Z0 = 50 * eye(2);

% ---- Read S-parameters ----
Z0 = 50 * eye(2);

[freq1, S_dut1] = read_sparams(files.dut1);
[~, S_short1] = read_sparams(files.short1);
[~, S_open1] = read_sparams(files.open1);

[freq2, S_dut2] = read_sparams(files.dut2);
[~, S_short2] = read_sparams(files.short2);
[~, S_open2] = read_sparams(files.open2);

% ---- De-embedding ----
S_deembed1 = deembed_sparams(S_dut1, S_short1, S_open1, Z0);
S_deembed2 = deembed_sparams(S_dut2, S_short2, S_open2, Z0);

% ---- Write outputs ----
write_sparams_csv('inductor_deembedded_1.csv', freq1, S_deembed1);
write_sparams_csv('inductor_deembedded_2.csv', freq2, S_deembed2);

% ---- Plot before/after ----
S_deembed1 = deembed_sparams(S_dut1, S_short1, S_open1, Z0);
S_deembed2 = deembed_sparams(S_dut2, S_short2, S_open2, Z0);

write_sparams_csv('inductor_deembedded_1.csv', freq1, S_deembed1);
write_sparams_csv('inductor_deembedded_2.csv', freq2, S_deembed2);

plot_before_after(freq1, S_dut1, S_deembed1, 'DUT 1');
plot_before_after(freq2, S_dut2, S_deembed2, 'DUT 2');

disp('De-embedding complete. Output written to:');
disp('  inductor_deembedded_1.csv');
disp('  inductor_deembedded_2.csv');

function [freq, S] = read_sparams(filename)
    % Read CSV and convert dB/deg S-params into complex 2x2xN matrix.
    data = readtable(filename);
    data = data(:, 1:min(9, width(data)));
    vals = table2array(data);

    freq = vals(:, 1);
    s11_db = vals(:, 2); s11_deg = vals(:, 3);
    s21_db = vals(:, 4); s21_deg = vals(:, 5);
    s12_db = vals(:, 6); s12_deg = vals(:, 7);
    s22_db = vals(:, 8); s22_deg = vals(:, 9);

    s11 = dbdeg_to_complex(s11_db, s11_deg);
    s21 = dbdeg_to_complex(s21_db, s21_deg);
    s12 = dbdeg_to_complex(s12_db, s12_deg);
    s22 = dbdeg_to_complex(s22_db, s22_deg);

    n = numel(freq);
    S = zeros(2, 2, n);
    S(1, 1, :) = reshape(s11, 1, 1, n);
    S(2, 1, :) = reshape(s21, 1, 1, n);
    S(1, 2, :) = reshape(s12, 1, 1, n);
    S(2, 2, :) = reshape(s22, 1, 1, n);
end

function S_deembed = deembed_sparams(S_dut, S_short, S_open, Z0)
    % Open/short de-embedding based on Y/Z conversions.
    n = size(S_dut, 3);
    S_deembed = zeros(size(S_dut));
    for k = 1:n
        Y_dut = s_to_y(S_dut(:, :, k), Z0);
        Y_short = s_to_y(S_short(:, :, k), Z0);
        Y_open = s_to_y(S_open(:, :, k), Z0);

        Y_dut_open = Y_dut - Y_open;
        Y_short_open = Y_short - Y_open;

        Z_dut_open = inv(Y_dut_open);
        Z_short_open = inv(Y_short_open);

        Z_dut = Z_dut_open - Z_short_open;

        S_deembed(:, :, k) = z_to_s(Z_dut, Z0);
    end
end

function y = s_to_y(S, Z0)
    % Convert S-parameters to Y-parameters.
    I = eye(2);
    y = (I - S) * (Z0 \ (I + S));
end

function S = z_to_s(Z, Z0)
    % Convert Z-parameters to S-parameters.
    I = eye(2);
    S = (Z - Z0) / (Z + Z0);
end

function c = dbdeg_to_complex(db, deg)
    % Convert magnitude (dB) and phase (deg) to complex value.
    mag = 10.^(db / 20);
    ang = deg2rad(deg);
    c = mag .* exp(1j * ang);
end

function write_sparams_csv(filename, freq, S)
    % Write complex S-parameters to CSV (dB/deg).
    n = numel(freq);
    s11 = squeeze(S(1, 1, :));
    s21 = squeeze(S(2, 1, :));
    s12 = squeeze(S(1, 2, :));
    s22 = squeeze(S(2, 2, :));

    out = table(...
        freq(:), ...
        20*log10(abs(s11)), rad2deg(angle(s11)), ...
        20*log10(abs(s21)), rad2deg(angle(s21)), ...
        20*log10(abs(s12)), rad2deg(angle(s12)), ...
        20*log10(abs(s22)), rad2deg(angle(s22)), ...
        'VariableNames', {'Freq_Hz', 'S11_dB', 'S11_deg', 'S21_dB', 'S21_deg', 'S12_dB', 'S12_deg', 'S22_dB', 'S22_deg'} ...
    );

    writetable(out, filename);
end

function plot_before_after(freq, S_before, S_after, labelText)
    % Plot S11 and S21 magnitude before/after de-embedding.
    s11_before = squeeze(S_before(1, 1, :));
    s21_before = squeeze(S_before(2, 1, :));
    s11_after = squeeze(S_after(1, 1, :));
    s21_after = squeeze(S_after(2, 1, :));

    figure('Name', ['S11 ' labelText], 'Color', 'w');
    plot(freq, 20*log10(abs(s11_before)), 'b-', 'LineWidth', 1.2); hold on;
    plot(freq, 20*log10(abs(s11_after)), 'r--', 'LineWidth', 1.2);
    grid on; xlabel('Frequency (Hz)'); ylabel('S11 (dB)');
    title(['S11 Before/After De-embedding - ' labelText]);
    legend('Before', 'After', 'Location', 'best');

    figure('Name', ['S21 ' labelText], 'Color', 'w');
    plot(freq, 20*log10(abs(s21_before)), 'b-', 'LineWidth', 1.2); hold on;
    plot(freq, 20*log10(abs(s21_after)), 'r--', 'LineWidth', 1.2);
    grid on; xlabel('Frequency (Hz)'); ylabel('S21 (dB)');
    title(['S21 Before/After De-embedding - ' labelText]);
    legend('Before', 'After', 'Location', 'best');
end
